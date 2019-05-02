
Instrument Templates
====================

General Instrument
------------------

.. automodule:: pysat.instruments.template_instrument
   :members: __doc__, init, default, load, list_files, list_remote_files, download, clean

NASA CDAWeb Instrument
----------------------

.. automodule:: pysat.instruments.template_cdaweb_instrument
   :members: __doc__, init, default, load, list_files, list_remote_files, download, clean


General Data Source Methods
===========================

NASA CDAWeb
-----------

.. automodule:: pysat.instruments.methods.nasa_cdaweb
   :members: __doc__, init, load, list_files, list_remote_files, download


Madrigal
--------

.. automodule:: pysat.instruments.methods.madrigal
   :members: __doc__, cedar_rules, load, download, filter_data_single_date


Demeter
-------

.. automodule:: pysat.instruments.methods.demeter
   :members: __doc__, download, bytes_to_float, load_general_header, load_location_parameters, load_attitude_parameters, load_binary_file, set_metadata


Supported Instruments
=====================

C/NOFS IVM
----------

.. automodule:: pysat.instruments.cnofs_ivm
   :members: __doc__

C/NOFS PLP
----------

.. automodule:: pysat.instruments.cnofs_plp
   :members: __doc__

C/NOFS VEFI
-----------

.. automodule:: pysat.instruments.cnofs_vefi
   :members: __doc__

CHAMP-STAR
----------

.. automodule:: pysat.instruments.champ_star
   :members: __doc__

COSMIC 2013 GPS
---------------

.. automodule:: pysat.instruments.cosmic2013_gps
   :members: __doc__

COSMIC GPS
----------

.. automodule:: pysat.instruments.cosmic_gps
   :members: __doc__

Demeter IAP
-----------

.. automodule:: pysat.instruments.demeter_iap
    :members: __doc__, add_drift_sat_coord, add_drift_lgm_coord, add_drift_geo_coord

DMSP IVM
--------

.. automodule:: pysat.instruments.dmsp_ivm
   :members: __doc__, smooth_ram_drifts, update_DMSP_ephemeris, add_drift_unit_vectors, add_drifts_polar_cap_x_y

ICON EUV
--------

.. automodule:: pysat.instruments.icon_euv
   :members: __doc__, remove_icon_names

ICON FUV
--------

.. automodule:: pysat.instruments.icon_fuv
   :members: __doc__, remove_icon_names

ICON IVM
--------

.. automodule:: pysat.instruments.icon_ivm
   :members: __doc__, remove_icon_names

ICON MIGHTI
-----------

.. automodule:: pysat.instruments.icon_mighti
   :members: __doc__, remove_icon_names

ISS-FPMU
--------

.. automodule:: pysat.instruments.iss_fpmu
   :members: __doc__

JRO ISR
-------

.. automodule:: pysat.instruments.jro_isr
    :members: __doc__

netCDF Pandas
-------------

.. automodule:: pysat.instruments.netcdf_pandas
   :members: __doc__, init, load, list_files, download

OMNI
----

.. automodule:: pysat.instruments.omni_hro
   :members: __doc__, calculate_clock_angle, calculate_imf_steadiness, time_shift_to_magnetic_poles

PYSAT SGP4
----------

.. automodule:: pysat.instruments.pysat_sgp4
   :members: __doc__, load, add_sc_attitude_vectors, calculate_ecef_velocity, add_quasi_dipole_coordinates, add_aacgm_coordinates, add_iri_thermal_plasma, add_hwm_winds_and_ecef_vectors, add_igrf, project_ecef_vector_onto_sc, project_hwm_onto_sc

ROCSAT-1 IVM
------------

.. automodule:: pysat.instruments.rocsat1_ivm
   :members: __doc__

SPORT IVM
---------

.. automodule:: pysat.instruments.sport_ivm
   :members: __doc__

SuperDARN
---------

.. automodule:: pysat.instruments.superdarn_grdex
   :members: __doc__

SuperMAG
--------

.. automodule:: pysat.instruments.supermag_magnetometer
   :members: __doc__

SW Dst
------

.. automodule:: pysat.instruments.sw_dst
   :members: __doc__

SW F107
-------

.. automodule:: pysat.instruments.sw_f107
   :members: __doc__

SW Kp
-----

.. automodule:: pysat.instruments.sw_kp
   :members: __doc__, filter_geoquiet

TIMED/SABER
---------

.. automodule:: pysat.instruments.timed_saber
   :members: __doc__

TIMED/SEE
---------

.. automodule:: pysat.instruments.timed_see
  :members: __doc__

UCAR TIEGCM
-----------

.. automodule:: pysat.instruments.ucar_tiegcm
   :members: __doc__
