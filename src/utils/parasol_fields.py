"""Standard lists of fields to get from PARASOL files."""

# All available fields
_ALL = [
    ("Data_Directional_Fields", "I443NP"),  # normalized radiance for channel 443NP
    ("Data_Directional_Fields", "I490P"),  # normalized radiance for channel 490P
    ("Data_Directional_Fields", "Q490P"),  # second component of Stokes Vector (Q) for channel 490P
    ("Data_Directional_Fields", "U490P"),  # third component of Stokes Vector (U) for channel 490P
    ("Data_Directional_Fields", "I565NP"),  # normalized radiance for channel 565NP
    ("Data_Directional_Fields", "I670P"),  # normalized radiance for channel 670P
    ("Data_Directional_Fields", "Q670P"),  # second component of Stokes Vector (Q) for channel 670P
    ("Data_Directional_Fields", "U670P"),  # third component of Stokes Vector (U) for channel 670P
    ("Data_Directional_Fields", "I763NP"),  # normalized radiance for channel 763NP
    ("Data_Directional_Fields", "I765NP"),  # normalized radiance for channel 765NP
    ("Data_Directional_Fields", "I865P"),  # normalized radiance for channel 865P
    ("Data_Directional_Fields", "Q865P"),  # second component of Stokes Vector (Q) for channel 865P
    ("Data_Directional_Fields", "U865P"),  # third component of Stokes Vector (U) for channel 865P
    ("Data_Directional_Fields", "I910NP"),  # normalized radiance for channel 910NP
    ("Data_Directional_Fields", "I1020NP"),  # normalized radiance for channel 1020NP
    ("Data_Directional_Fields", "phi"),  # relative azimuth angle of the pixel center  for filter 670P2
    ("Data_Directional_Fields", "thetas"),  # solar zenith angle of the pixel center
    ("Data_Directional_Fields", "thetav"),  # view zenith angle of the pixel center  for filter 670P2
    ("Data_Fields", "Nviews"),  # number of available view directions [1-16]
    ("Data_Fields", "cloud_indicator"),  # rough cloud indicator: clear (0), cloudy (100), undetermined (50)
    ("Data_Fields", "phis"),  # solar azimuth angle of the pixel center
    ("Geolocation_Fields", "Latitude"),  # pixel center latitude
    ("Geolocation_Fields", "Longitude"),  # pixel center longitude
    ("Geolocation_Fields", "land_sea_flag"),  # land sea flag (0:sea, 100:land, 50:mixed)
    ("Geolocation_Fields", "surface_altitude"),  # pixel center surface altitude
    # Potential error in the attitude data (0:0.01; 1:0.05; 2:0.1; 3:0.15; 4:0.25; 5:0.50; 6:1; 7: >1 ).
    ("Quality_Flags_Directional_Fields", "Quality_Flags_01"),
    # Anomaly in the correction for optic polarization.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_02"),
    # Pixel saturated/lacking in the 4x4 window used for bicubic interpolation.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_03"),
    # Pixel saturated/lacking in the 4x4 window used for bicubic interpolation.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_04"),
    # Pixel saturated/lacking in the 4x4 window used for bicubic interpolation.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_05"),
    # Pixel saturated/lacking in the 4x4 window used for bicubic interpolation.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_06"),
    # CCD pixel may be degraded (matrix border).
    ("Quality_Flags_Directional_Fields", "Quality_Flags_07"),
    # CCD pixel may be degraded (matrix border).
    ("Quality_Flags_Directional_Fields", "Quality_Flags_08"),
    # CCD pixel may be degraded (matrix border).
    ("Quality_Flags_Directional_Fields", "Quality_Flags_09"),
    # CCD pixel may be degraded (matrix border).
    ("Quality_Flags_Directional_Fields", "Quality_Flags_10"),
    # Stray light correction (type 1) greater than a threshold. The thresholds are defined by the ocean color mission requirements.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_11"),
    # Stray light correction (type 1) greater than a threshold. The thresholds are defined by the other mission requirements.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_12"),
    # Stray light correction (type 2) greater than a threshold. The thresholds are defined by the ocean color mission requirements.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_13"),
    # Stray light correction (type 2) greater than a threshold. The thresholds are defined by the other mission requirements.
    ("Quality_Flags_Directional_Fields", "Quality_Flags_14"),
]

# The default set, which contains all of the wavelengths, but leaves out quality flags and phi
_DEFAULT = [
    ("Data_Directional_Fields", "I443NP"),
    ("Data_Directional_Fields", "I490P"),
    ("Data_Directional_Fields", "Q490P"),
    ("Data_Directional_Fields", "U490P"),
    ("Data_Directional_Fields", "I565NP"),
    ("Data_Directional_Fields", "I670P"),
    ("Data_Directional_Fields", "Q670P"),
    ("Data_Directional_Fields", "U670P"),
    ("Data_Directional_Fields", "I763NP"),
    ("Data_Directional_Fields", "I765NP"),
    ("Data_Directional_Fields", "I865P"),
    ("Data_Directional_Fields", "Q865P"),
    ("Data_Directional_Fields", "U865P"),
    ("Data_Directional_Fields", "I910NP"),
    ("Data_Directional_Fields", "I1020NP"),
    ("Data_Directional_Fields", "phi"),
    ("Data_Directional_Fields", "thetas"),
    ("Data_Directional_Fields", "thetav"),
    ("Data_Fields", "Nviews"),
    ("Data_Fields", "cloud_indicator"),
    ("Geolocation_Fields", "Latitude"),
    ("Geolocation_Fields", "Longitude"),
    ("Geolocation_Fields", "land_sea_flag"),
    ("Geolocation_Fields", "surface_altitude"),
]

# all directional fields
_DIRECTIONAL = [
    ("Data_Directional_Fields", "I443NP"),
    ("Data_Directional_Fields", "I490P"),
    ("Data_Directional_Fields", "Q490P"),
    ("Data_Directional_Fields", "U490P"),
    ("Data_Directional_Fields", "I565NP"),
    ("Data_Directional_Fields", "I670P"),
    ("Data_Directional_Fields", "Q670P"),
    ("Data_Directional_Fields", "U670P"),
    ("Data_Directional_Fields", "I763NP"),
    ("Data_Directional_Fields", "I765NP"),
    ("Data_Directional_Fields", "I865P"),
    ("Data_Directional_Fields", "Q865P"),
    ("Data_Directional_Fields", "U865P"),
    ("Data_Directional_Fields", "I910NP"),
    ("Data_Directional_Fields", "I1020NP"),
    ("Data_Directional_Fields", "phi"),
    ("Data_Directional_Fields", "thetas"),
    ("Data_Directional_Fields", "thetav"),
]

# The minimal set of fields to use for debugging
_MINIMAL = [
    ("Data_Directional_Fields", "I865NP"),
    ("Data_Fields", "Nviews"),
    ("Data_Fields", "cloud_indicator"),
    ("Geolocation_Fields", "Latitude"),
    ("Geolocation_Fields", "Longitude"),
]

_BANDS = {
    443: ["I443NP"],
    490: ["I490P", "Q490P", "U490P"],
    565: ["I565NP"],
    670: ["I670P", "Q670P", "U670P"],
    763: ["I763NP"],
    765: ["I765NP"],
    865: ["I865P", "Q865P", "U865P"],
    910: ["I910NP"],
    1020: ["I1020NP"],
}
_SINGLE_BAND_OTHER_FIELDS = [
    ("Data_Directional_Fields", "phi"),
    ("Data_Directional_Fields", "thetas"),
    ("Data_Directional_Fields", "thetav"),
]

FIELD_DICT = {
    "all": _ALL,
    "default": _DEFAULT,
    "directional": _DIRECTIONAL,
    "minimal": _MINIMAL,
}
for band_wl, band_fields in _BANDS.items():
    fields = [("Data_Directional_Fields", field) for field in band_fields] + _SINGLE_BAND_OTHER_FIELDS
    FIELD_DICT[f"single_band_{band_wl}"] = fields
