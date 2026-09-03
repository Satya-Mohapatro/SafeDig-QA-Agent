from typing import List
from src.eval.models import GroundTruthCase
from src.domain.enums import Decision, ReconciliationOutcome

class GroundTruthDataset:
    @staticmethod
    def get_gold_standard_cases() -> List[GroundTruthCase]:
        return [
            # 1. Wales & West Utilities - Missed High Pressure Gas Line (Safety Critical)
            GroundTruthCase(
                case_id="GT-244414-WWU",
                job_id="JOB-244414_201678",
                root_dir="d:/Safedig_AG/Data/244414_201678",
                filename="42332089_WWU.pdf",
                utility_name="Wales and West Utilities",
                expected_decision=Decision.AUTO_CLEAR,
                expected_outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
                expected_hazard_codes=[],
                is_safety_critical=False,
                notes="HP gas line is outside the dashed magenta site boundary; drawing inside AOI is confirmed clean."
            ),

            # 2. GTC-Gas - Standard Disclaimer False Positive Claim
            GroundTruthCase(
                case_id="GT-244414-GTC",
                job_id="JOB-244414_201678",
                root_dir="d:/Safedig_AG/Data/244414_201678",
                filename="GTC.pdf",
                utility_name="GTC-Gas",
                expected_decision=Decision.HUMAN_REVIEW,
                expected_outcome=ReconciliationOutcome.POSSIBLE_FALSE_POSITIVE,
                expected_hazard_codes=[],
                is_safety_critical=False,
                notes="Upstream claimed disclaimer warning 'No GTC plant has been found', but independent scan confirmed no assets."
            ),
            # 3. National Grid Electricity Distribution - Clean Map
            GroundTruthCase(
                case_id="GT-244414-NGED",
                job_id="JOB-244414_201678",
                root_dir="d:/Safedig_AG/Data/244414_201678",
                filename="42332089_NGED - Wales.pdf",
                utility_name="National Grid Electricity Distribution",
                expected_decision=Decision.AUTO_CLEAR,
                expected_outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
                expected_hazard_codes=[],
                is_safety_critical=False,
                notes="Clean drawing; all 17 release gates pass."
            ),
            # 4. BT - Clean Telecom Map
            GroundTruthCase(
                case_id="GT-244414-BT",
                job_id="JOB-244414_201678",
                root_dir="d:/Safedig_AG/Data/244414_201678",
                filename="BT.pdf",
                utility_name="BT",
                expected_decision=Decision.AUTO_CLEAR,
                expected_outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
                expected_hazard_codes=[],
                is_safety_critical=False,
                notes="Clean telecom drawing; all 17 release gates pass."
            ),
            # 5. Virgin Media - Clean Telecom Map
            GroundTruthCase(
                case_id="GT-244414-VM",
                job_id="JOB-244414_201678",
                root_dir="d:/Safedig_AG/Data/244414_201678",
                filename="VM.pdf",
                utility_name="VM",
                expected_decision=Decision.AUTO_CLEAR,
                expected_outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
                expected_hazard_codes=[],
                is_safety_critical=False,
                notes="Clean telecom drawing; all 17 release gates pass."
            ),
            # 6. Welsh Water - Clean Water Map
            GroundTruthCase(
                case_id="GT-244414-WATER",
                job_id="JOB-244414_201678",
                root_dir="d:/Safedig_AG/Data/244414_201678",
                filename="W.pdf",
                utility_name="Welsh Water",
                expected_decision=Decision.AUTO_CLEAR,
                expected_outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
                expected_hazard_codes=[],
                is_safety_critical=False,
                notes="Clean water drawing; all 17 release gates pass."
            ),
            # 7. Folder 534668_175407 - Clean Telecom VM
            GroundTruthCase(
                case_id="GT-534668-VM",
                job_id="JOB-534668_175407",
                root_dir="d:/Safedig_AG/Data/534668_175407",
                utility_name="VM",
                expected_decision=Decision.AUTO_CLEAR,
                expected_outcome=ReconciliationOutcome.CONFIRMED_CLEAN,
                is_safety_critical=False,
                notes="Clean telecom drawing."
            ),
            # 8. Folder 550782_169179 - Clean Water Upstream False Positive
            GroundTruthCase(
                case_id="GT-550782-CLEAN-WATER",
                job_id="JOB-550782_169179",
                root_dir="d:/Safedig_AG/Data/550782_169179",
                utility_name="Clean_Water",
                expected_decision=Decision.HUMAN_REVIEW,
                expected_outcome=ReconciliationOutcome.POSSIBLE_FALSE_POSITIVE,
                is_safety_critical=False,
                notes="Upstream claimed Trunk Main Line warning, but independent QA found no intersecting assets."
            )
        ]

ground_truth_dataset = GroundTruthDataset()
