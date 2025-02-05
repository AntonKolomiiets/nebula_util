import re

# Flexible regex pattern
# pattern = r"^\d{2}\.\d{2}\.\d{4} (?:F-(?:Video|Static))_N-[\w\+\-()]+(?:_[\w\+\-()]*)*_Co-\d{2,3}.*?(?:_Cm-[A-Z]{2,3})?_De-[A-Z]{2,3}$"
pattern = r"(^\d{2}\.\d{2}\.\d{4} (?:F-(?:Video|Static))_N-[\w\+\-()]+(?:_[\w\+\-()]*)*_Co-\d{2,3}.*?(?:_Cm-[A-Z]{2,3})?_De-[A-Z]{2,3})(?:-\d{1,2})?$"

# Example test cases
test_strings = [
    "13.01.2025 F-Static_N-var-dram-shift5_Co-39_To-36_P-08_Fe-04_H-VF-094_D-03_CTA-27_V-01_Cm-VF_De-MA-02",
    "13.01.2025 F-Static_N-var-dram-shift5_Co-39_To-36_P-08_Fe-04_H-VF-094_D-03_CTA-27_V-01_Cm-VF_De-MA-4",
    "13.01.2025 F-Static_N-var-dram-shift5_Co-39_To-36_P-08_Fe-04_H-VF-094_D-03_CTA-27_V-01_Cm-VF_De-MA",
    "13.01.2025 F-Static_N-var-dram-shift5_Co-39_To-36_P-08_Fe-04_H-VF-094_D-03_CTA-27_V-01_Cm-VF_De-MA-01"
    "30.12.2024 F-Static_N-var-dram-shift3_Co-39_To-36_P-08_Fe-04_H-VF-094_D-03_CTA-27_V-08_Cm-VF_De-KK-03-AI",
    "29.01.2025 F-Video_N-some-example_Co-00_H-XX-777_P-21_S-12_Cm-XY_De-ZZ",
    "23.10.2024 F-Static_N-sample_Co-07_S-99_Cm-AB_De-KO",
    "Invalid Example String"
]

# Testing regex
# for string in test_strings:
#     if re.match(pattern, string):
#         print(f"✅ Matches: {string}")
#     else:
#         print(f"❌ Does not match: {string}")
