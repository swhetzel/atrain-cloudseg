"""The A-Train dataset consists of input/output pairs where input is multi-angle polarimetry from PARASOL/POLDER and
output is cloud scenario labels from the CALTRACK CLDCLASS product.
"""

import json
import os
import pickle
import random
import sys
from typing import Callable

import numpy as np
import torch
import torchvision.transforms.functional as TF
from torch.utils.data import Dataset

if "./src" not in sys.path:
    sys.path.insert(0, "./src")  # TO DO: change this once it's a package
from datasets.normalization import ATRAIN_MEANS, ATRAIN_STDS

ALL_METRICS = [
    "cloud_mask_accuracy",
    "cloud_scenario_accuracy",
    "cloudtop_height_bin_accuracy",
    "cloudtop_height_bin_offset_error",
]
MASK_ONLY_METRICS = ["cloud_mask_accuracy", "cloudtop_height_bin_accuracy", "cloudtop_height_bin_offset_error"]
SQUASH_BINS_METRICS = ["cloud_mask_accuracy"]


class ATrain(Dataset):
    """The A-Train Dataset."""

    def __init__(
        self,
        mode: str,
        angles_to_omit: list = [],
        fields: list = [],
        get_nondir: bool = False,
        get_flags: bool = False,
        split_name: str = "split_default",
    ) -> None:
        """Create an A-Train Dataset.

        Args:
            mode: Which mode to use for training. In the default split, this must be 'train' or 'val'.
            fields: List of fields to get in this dataset.
            get_nondir: Get non-directional fields for each instance. Considerably slows down data loading. Defaults to
                        False.
            get_flags: Get flags for the cloud scenario output. Defaults to False.
            split_name: The name of the split file to use.
        """
        super().__init__()
        assert all([a >= 0 and a < 16 for a in angles_to_omit])
        self.mode = mode
        self.angles_to_omit = angles_to_omit
        self.num_angles = 16 - len(angles_to_omit)
        self.fields = [list(f) for f in fields]
        self.get_nondir = get_nondir
        self.get_flags = get_flags
        self.split_name = split_name

        self.dataset_root = os.path.join(os.path.dirname(__file__), "..", "..", "data", "atrain")
        self.datagen_info = json.load(open(os.path.join(self.dataset_root, "dataset_generation_info.json")))
        # read instance info file, make keys into integers
        self.instance_info = json.load(open(os.path.join(self.dataset_root, "instance_info.json")))
        self.instance_info = {int(k): v for k, v in self.instance_info.items()}
        # load our split, get the instance ids
        self.split = json.load(open(os.path.join(self.dataset_root, f"{self.split_name}.json")))
        self.instance_ids = list(self.split[self.mode])

        # pre-compute length so we don't have to later; it won't change
        self.len = len(self.instance_ids)

        # get index of just the multi-angle fields
        self.multi_angle_idx = []
        self.nondir_idx = []
        self.nondir_fields = []
        channel_idx = 0
        for i in range(len(self.datagen_info["par_fields"])):
            field = self.datagen_info["par_fields"][i]
            if field[0] == "Data_Directional_Fields":
                if field in self.fields:
                    self.multi_angle_idx += [
                        channel_idx + angle_idx for angle_idx in range(16) if angle_idx not in self.angles_to_omit
                    ]
                channel_idx += 16
            else:
                if field in self.fields:
                    self.nondir_fields.append(field[1])
                    self.nondir_idx.append(channel_idx)
                channel_idx += 1
        self.multi_angle_idx = np.array(self.multi_angle_idx)
        self.nondir_idx = np.array(self.nondir_idx)

    def __len__(self) -> int:
        """Get the length of this dataset."""
        return self.len

    def _patch_idx_to_interp(self, patch_idx: tuple[np.array, np.array]) -> tuple[np.array, np.array]:
        """Convert the patch index to interpolation corners / weights to apply to model output.

        Args:
            patch_idx: A tuple of numpy arrays for the y- and x- coordinates of output values in the input array.

        Returns:
            interp_corners: The locations of corners to use for interpolation
            interp_weights: The weights for these corners, summing to 1 for each box
        """
        idx_y, idx_x = patch_idx

        top_bottom = np.stack([np.floor(idx_y).astype(int), np.ceil(idx_y).astype(int)], axis=1)
        left_right = np.stack([np.floor(idx_x).astype(int), np.ceil(idx_x).astype(int)], axis=1)

        topleft = np.stack([top_bottom[:, 0], left_right[:, 0]], axis=1)
        topright = np.stack([top_bottom[:, 0], left_right[:, 1]], axis=1)
        bottomleft = np.stack([top_bottom[:, 1], left_right[:, 0]], axis=1)
        bottomright = np.stack([top_bottom[:, 1], left_right[:, 1]], axis=1)

        interp_corners = np.stack([topleft, topright, bottomleft, bottomright], axis=1)
        weight_y = 1 - np.abs(interp_corners[:, :, 0] - np.stack([idx_y] * 4, axis=1))
        weight_x = 1 - np.abs(interp_corners[:, :, 1] - np.stack([idx_x] * 4, axis=1))
        interp_weights = np.expand_dims(weight_y * weight_x, axis=2)

        return interp_corners, interp_weights

    def __getitem__(self, idx: int) -> dict:
        """Get the item at the specified index."""
        inst_id = self.instance_ids[idx]
        inst = self.instance_info[inst_id]
        parasol_arr = np.load(os.path.join(self.dataset_root, inst["input_path"]))
        input_arr = parasol_arr[:, :, self.multi_angle_idx]
        input_arr = np.transpose(np.clip(input_arr, 0, 1), (2, 0, 1))
        output_dict = pickle.load(open(os.path.join(self.dataset_root, inst["output_path"]), "rb"))
        assert inst_id == output_dict.pop("instance_id")

        patch_idx = output_dict.pop("patch_idx")
        interp_corners, interp_weights = self._patch_idx_to_interp(patch_idx)  # (p, 4, 3)

        cloud_scenario_flags = output_dict.pop("cloud_scenario")
        cloud_scenario = cloud_scenario_flags.pop("cloud_scenario")  # (p, 125)

        item = {
            "instance_id": inst_id,
            "input": {
                "sensor_input": input_arr,
                "interp": {
                    "corners": interp_corners,
                    "weights": interp_weights,
                },
            },
            "output": {"cloud_scenario": cloud_scenario},
        }

        if self.get_nondir:
            nondir_input = parasol_arr[:, :, self.nondir_idx]
            item["input"]["nondirectional_fields"] = {}
            for i in range(len(self.nondir_fields)):
                nondir_field = self.nondir_fields[i]
                item["input"]["nondirectional_fields"][nondir_field] = nondir_input[:, :, i]
            for f in ["lat", "lon", "height", "time"]:
                item["output"][f] = output_dict.pop(f)

        if self.get_flags:
            item["output"]["cloud_scenario_flags"] = cloud_scenario_flags

        return item

    def evaluate(self, predictions: dict, metrics: list[str] = ALL_METRICS) -> dict:
        """Evaluate a set of predictions w.r.t. a set of metrics on this dataset.

        Args:
            predictions: The predictions to evaluate.
            metrics: The list of metrics to evaluate.

        Returns:
            metrics: The metrics' evaluations on the provided predictions.
        """
        metrics = {m: [] for m in metrics}
        for inst_id in self.instance_ids:
            if inst_id not in predictions:
                for m in metrics:
                    metrics[m].append(0)

            inst = self.instance_info[inst_id]
            pred = predictions[inst_id]

            gt_labels = pickle.load(open(os.path.join(self.dataset_root, inst["output_path"]), "rb"))
            gt_cloud_scenario = gt_labels["cloud_scenario"]["cloud_scenario"]

            # if we're squashing bins
            if pred.shape[1] == 1:
                gt_cloud_scenario = np.sum(gt_cloud_scenario, axis=1, keepdims=True) > 0

            gt_cloud_mask = (gt_cloud_scenario > 0).any(axis=1)
            pred_cloud_mask = (pred > 0).any(axis=1)

            def _min(a):
                if a.shape[0] == 0:
                    return -1
                return np.min(a)

            h_bins_pred = np.array([_min(np.where(pred[i].cpu().detach().numpy())[0]) for i in range(pred.shape[0])])
            h_bins_gt = np.array([_min(np.where(gt_cloud_scenario[i])[0]) for i in range(gt_cloud_scenario.shape[0])])

            if "cloud_mask_accuracy" in metrics:
                # cloud mask accuracy := proportion of pixels correctly identified as cloud / not cloud
                metrics["cloud_mask_accuracy"].append(np.mean(gt_cloud_mask == pred_cloud_mask.cpu().detach().numpy()))

            if "cloud_scenario_accuracy" in metrics:
                # cloud scenario accuracy := proportion of pixel + height bin combinations whose cloud scenario is
                #   correctly identified
                metrics["cloud_scenario_accuracy"].append(np.mean(gt_cloud_scenario == pred.cpu().detach().numpy()))

            if "cloudtop_height_bin_accuracy" in metrics:
                # cloud-top height bin accuracy := proportion of pixels whose highest cloud bin is correctly identified
                metrics["cloudtop_height_bin_accuracy"].append(np.mean(h_bins_pred == h_bins_gt))

            if "cloudtop_height_bin_offset_error" in metrics:
                # cloud-top height bin offset := average distance between predicted and GT cloud-top height, only
                #   computed for points pixels where both prediction and GT have clouds
                both_clouds = pred_cloud_mask.cpu().detach().numpy() * gt_cloud_mask
                height_bin_offsets = np.abs(h_bins_pred[both_clouds] - h_bins_gt[both_clouds])
                metrics["cloudtop_height_bin_offset_error"].append(np.mean(height_bin_offsets))

        metrics["instance_ids"] = list(self.instance_info.keys())
        metrics = {k: np.array(v) for k, v in metrics.items()}
        return metrics


def collate_atrain(batch: list) -> dict:
    """Collate a batch from the A-Train Dataset.

    Args:
        batch: A list of instances, where each instance is a dictionary.

    Returns:
        coll_batch: The collated batch.
    """
    coll_batch = {}
    inst_ids = []
    sensor_input = []
    b_idx = []
    interp_corners = []
    interp_weights = []
    cloud_scenario = []
    for inst_idx in range(len(batch)):
        inst = batch[inst_idx]
        inst_ids.append(inst["instance_id"])
        sensor_input.append(torch.as_tensor(inst["input"]["sensor_input"], dtype=torch.float))
        b_idx.append(torch.as_tensor([inst_idx], dtype=torch.long).repeat(inst["input"]["interp"]["corners"].shape[0]))
        # Pre-compute interpolation corners and weights so that applying the interpolated loss is quick and easy
        interp_corners.append(torch.as_tensor(inst["input"]["interp"]["corners"], dtype=torch.long))
        interp_weights.append(torch.as_tensor(inst["input"]["interp"]["weights"], dtype=torch.float))
        cloud_scenario.append(torch.as_tensor(inst["output"]["cloud_scenario"], dtype=torch.long))
    coll_batch = {
        "instance_id": torch.as_tensor(inst_ids),
        "input": {
            "sensor_input": torch.stack(sensor_input, dim=0),
            "interp": {
                "batch_idx": torch.cat(b_idx, dim=0),
                "corners": torch.cat(interp_corners, dim=0),
                "weights": torch.cat(interp_weights, dim=0),
            },
        },
        "output": {"cloud_scenario": torch.cat(cloud_scenario, dim=0)},
    }

    if "nondirectional_fields" in batch[0]["input"]:
        nondir_fields = {field_name: [] for field_name in batch[0]["input"]["nondirectional_fields"]}
        for instance in batch:
            for field_name in nondir_fields:
                nondir_fields[field_name].append(
                    torch.as_tensor(instance["input"]["nondirectional_fields"][field_name])
                )
        coll_batch["input"]["nondirectional_fields"] = {k: torch.stack(v, dim=0) for k, v in nondir_fields.items()}
        geom_output = {f: [] for f in ["lat", "lon", "height", "time"]}
        for instance in batch:
            for f in geom_output:
                geom_output[f].append(torch.as_tensor(instance["output"][f]))
        coll_batch["output"]["geometry"] = {k: torch.cat(v, dim=0) for k, v in geom_output.items()}

    if "cloud_scenario_flags" in batch[0]["output"]:
        flags = {flag_name: [] for flag_name in batch[0]["output"]["cloud_scenario_flags"]}
        for instance in batch:
            for flag_name in flags:
                flags[flag_name].append(torch.as_tensor(instance["output"]["cloud_scenario_flags"][flag_name]))
        coll_batch["output"]["cloud_scenario_flags"] = {k: torch.cat(v, dim=0) for k, v in flags.items()}

    return coll_batch


def interp_atrain_output(batch: dict, out: torch.Tensor) -> torch.Tensor:
    """Interpolate output from a model to line up with the labels in a batch.

    Args:
        batch: A batch of instances from the A-Train dataset.
        out: The output of a model (same spatial resolution as input) which gets interpolated at labeled locations.

    Returns:
        out_interp: The interpolated output.
    """
    out = out.permute(0, 2, 3, 1)  # (B, H, W, C)

    # repeat the batch index for the 4 interp corners
    batch_idx = batch["input"]["interp"]["batch_idx"].expand(4, -1).T.reshape(-1)

    # height and width
    patch_shape = batch["input"]["sensor_input"].shape[-2:]

    # index to the 4 interp corners
    corner_idx = batch["input"]["interp"]["corners"]
    # keep the corners in bounds
    corner_idx[corner_idx[:, :, 0] < 0] = 0  # too high
    corner_idx[corner_idx[:, :, 0] >= patch_shape[0]] = patch_shape[0] - 1  # too low
    corner_idx[corner_idx[:, :, 1] < 0] = 0  # too far left
    corner_idx[corner_idx[:, :, 1] >= patch_shape[1]] = patch_shape[1] - 1  # too far right
    # get it as a flat index
    corner_idx = corner_idx[:, :, 0] * patch_shape[0] + corner_idx[:, :, 1]
    corner_idx = corner_idx.reshape(-1)

    # add the batch index to get the overall index
    idx = batch_idx * patch_shape[0] * patch_shape[1] + corner_idx

    # get the corner values
    out_corners = out.reshape(-1, out.shape[3])[idx]

    # get the weights of each corner
    weights = batch["input"]["interp"]["weights"].view(-1)

    # get the weighted corner values
    out_corners_weighted = weights.reshape(-1, 1) * out_corners
    out_corners_weighted = out_corners_weighted.view(weights.shape[0] // 4, 4, out_corners.shape[1])

    # sum up the weighted corner values to get final interpolated values
    out_interp = torch.sum(out_corners_weighted, dim=1)
    return out_interp


def get_norm_transform(multi_angle_idx: list) -> Callable:
    """Normalization transform. Normalizes sensor input by the A-Train means and standard deviations."""
    means = ATRAIN_MEANS[multi_angle_idx]
    stds = ATRAIN_STDS[multi_angle_idx]

    def norm_transform(batch: dict) -> dict:
        batch["input"]["sensor_input"] = TF.normalize(batch["input"]["sensor_input"], means, stds)
        return batch

    return norm_transform


def random_hflip(batch: dict) -> dict:
    """Random horizontal flip trnasform. Also flips the interpolation corners."""
    if random.random() > 0.5:
        batch["input"]["sensor_input"] = TF.hflip(batch["input"]["sensor_input"])
        w = batch["input"]["sensor_input"].shape[-1]
        corners_x = batch["input"]["interp"]["corners"][..., 0]
        corners_x = w - corners_x - 1
        batch["input"]["interp"]["corners"][..., 0] = corners_x
    return batch


def random_vflip(batch: dict) -> dict:
    """Random vertical flip trnasform. Also flips the interpolation corners."""
    if random.random() > 0.5:
        batch["input"]["sensor_input"] = TF.vflip(batch["input"]["sensor_input"])
        h = batch["input"]["sensor_input"].shape[-2]
        corners_y = batch["input"]["interp"]["corners"][..., 1]
        corners_y = h - corners_y - 1
        batch["input"]["interp"]["corners"][..., 1] = corners_y
    return batch


def get_transforms(mode: str, multi_angle_idx: list) -> list:
    """Get the list of transforms for either 'train' or 'val'.

    Args:
        mode: Specifies 'train' or 'val'.

    Returns:
        transforms: The list of transform functions.
    """
    if mode == "train":
        transforms = [get_norm_transform(multi_angle_idx), random_hflip, random_vflip]
    elif mode == "val":
        transforms = [get_norm_transform(multi_angle_idx)]
    return transforms
