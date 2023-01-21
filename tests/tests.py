import os

from pyfitness.load_data import fit2dict, fit2df, fit2csv, fit2excel
from pyfitness.dynamics import simulator, max_climb


def test_fit2dict():
    fitfile = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    fit_dict = fit2dict(fitfile)
    # print(fit_dict['header'])
    assert fit_dict['header']['profile_ver'] == (21, 72)
    assert len(fit_dict['records']) == 3033
    assert len(fit_dict['events']) == 248
    assert len(fit_dict['sessions']) == 1
    assert len(fit_dict['other_records']) == 17


def test_fit2df():
    fit1 = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    fit2 = "testdata/cheats/pedal_calibration/Zwift_KickrBikeV1_TruePower_Dec_20_2022.fit"
    fit3 = "testdata/indoor/10k_vEveresting.fit"
    fit4 = "testdata/Luciano/Outdoor/Luciano_indoor_climb_528m_distance_22.98km_power5_291.fit"
    for fit in [fit1, fit2, fit3, fit4]:
        df = fit2df(fit)
        assert len(df) > 0

def test_fit2csv():
    fitfile = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    outfile = "testdata/tempfiles/tempfile.csv"
    fit2csv(fitfile, outfile)
    assert os.path.exists(outfile)


def test_fit2excel():
    try:
        import openpyxl
    except:
        return
    fitfile = "testdata/cheats/pedal_calibration/Garmin_Assioma_200mm_test_Dec_20_2022.fit"
    outfile = "testdata/cheats/tempfile.xlsx"
    fit2excel(fitfile, outfile)
    assert os.path.exists(outfile)

def test_simulator():
    """Just testing that it runs"""
    fit1 = "testdata/cheats/pedal_calibration/Zwift_KickrBikeV1_TruePower_Dec_20_2022.fit"
    fit2 = "testdata/indoor/10k_vEveresting.fit"
    fit3 = "testdata/Luciano/Outdoor/Luciano_indoor_climb_528m_distance_22.98km_power5_291.fit"
    for fit in [fit1, fit2, fit3]:
        df = fit2df(fit)
        sim = simulator(df, rider_weight=70, bike_weight=10, wind_speed=3, wind_direction=3, temperature=20.1,
                       drag_coefficient=0.8, frontal_area=0.565, rolling_resistance=0.005, efficiency_loss=0.04)
