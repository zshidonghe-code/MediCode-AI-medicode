"""DRG Grouper unit tests — no server required."""
import pytest

from src.services.drg_grouper.grouper import (
    ADRG_DEFS,
    MDC_NAMES,
    DRGGrouper,
)


@pytest.fixture
def grouper():
    return DRGGrouper()


def test_determine_mdc_circulatory(grouper):
    mdc, name = grouper.determine_mdc("I21.900")
    assert mdc == "MDCE", f"Expected MDCE for AMI, got {mdc}"
    assert "循环" in name


def test_determine_mdc_respiratory(grouper):
    mdc, name = grouper.determine_mdc("J18.900")
    assert mdc == "MDCD", f"Expected MDCD for pneumonia, got {mdc}"


def test_determine_mdc_pregnancy(grouper):
    mdc, name = grouper.determine_mdc("O80.000")
    assert mdc == "MDCN"


def test_determine_mdc_empty_code(grouper):
    mdc, name = grouper.determine_mdc("")
    assert mdc == "MDCZ"


def test_determine_mdc_none_code():
    g = DRGGrouper()
    mdc, name = g.determine_mdc("")
    assert mdc == "MDCZ"


def test_determine_mdc_neuro(grouper):
    mdc, name = grouper.determine_mdc("G40.900")
    assert mdc == "MDCA", f"Expected MDCA for epilepsy, got {mdc}"


def test_cc_flag_mcc(grouper):
    result = grouper.determine_cc_flag(["I50.900", "I10.x00"])
    assert result == "MCC"


def test_cc_flag_cc(grouper):
    result = grouper.determine_cc_flag(["E11.900", "I10.x00"])
    assert result == "CC"


def test_cc_flag_none(grouper):
    result = grouper.determine_cc_flag(["Z00.000"])
    assert result == "无"


def test_group_pci_stemi(grouper):
    result = grouper.group(
        primary_diag_code="I21.900",
        secondary_diag_codes=["I25.100", "I10.x00", "E11.900"],
        procedure_codes=["36.0700"],
        patient_info={"age": 65, "gender": "male", "days_of_stay": 7},
    )
    assert result.mdc == "MDCE"
    assert result.is_surgical is True
    assert result.drg_code.startswith("FC")
    assert result.weight > 2.0


def test_group_pneumonia_medical(grouper):
    result = grouper.group(
        primary_diag_code="J18.900",
        secondary_diag_codes=[],
        procedure_codes=[],
        patient_info={"age": 45, "gender": "female", "days_of_stay": 8},
    )
    assert result.is_surgical is False
    assert result.weight < 2.0


def test_group_with_mcc_weights_more(grouper):
    without_mcc = grouper.group(
        primary_diag_code="I21.900",
        secondary_diag_codes=["I10.x00"],
        procedure_codes=["36.0700"],
        patient_info={"days_of_stay": 7},
    )
    with_mcc = grouper.group(
        primary_diag_code="I21.900",
        secondary_diag_codes=["I10.x00", "I50.900"],
        procedure_codes=["36.0700"],
        patient_info={"days_of_stay": 7},
    )
    assert with_mcc.weight > without_mcc.weight


def test_group_none_days_of_stay(grouper):
    result = grouper.group(
        primary_diag_code="J18.900",
        secondary_diag_codes=[],
        procedure_codes=[],
        patient_info={"days_of_stay": None},
    )
    assert result.estimated_payment > 0


def test_group_no_patient_info(grouper):
    result = grouper.group(
        primary_diag_code="J18.900",
        secondary_diag_codes=[],
        procedure_codes=[],
        patient_info={},
    )
    assert result.estimated_payment > 0


def test_icd_code_with_dots(grouper):
    mdc, name = grouper.determine_mdc("I21.9")
    assert mdc == "MDCE"


def test_drg_suffix_mapping(grouper):
    no_cc = grouper.group(
        primary_diag_code="J18.900",
        secondary_diag_codes=[],
        procedure_codes=[],
        patient_info={},
    )
    assert no_cc.drg_code.endswith("5") or no_cc.drg_code == "MDCZ-NA"


def test_neonatal_procedure_does_not_match_circulatory_adrg(grouper):
    result = grouper.group(
        primary_diag_code="P22.0",
        secondary_diag_codes=[],
        procedure_codes=["38.0"],
        patient_info={"age": 0, "days_of_stay": 5},
    )

    assert result.mdc == "MDCO"
    assert result.adrg == "PA1"


def test_all_adrg_definitions_have_known_mdc():
    unmapped = [
        code
        for mdc, code, _name, _is_surgical, _triggers, _weight in ADRG_DEFS
        if mdc not in MDC_NAMES
    ]

    assert unmapped == []


def test_representative_adrg_definitions_belong_to_expected_mdc():
    definition_mdc = {code: mdc for mdc, code, *_rest in ADRG_DEFS}

    assert definition_mdc["AA1"] == "MDCA"
    assert definition_mdc["BR1"] == "MDCA"
    assert definition_mdc["RA1"] == "MDCQ"
    assert definition_mdc["RR2"] == "MDCR"
    assert definition_mdc["SR1"] == "MDCS"
