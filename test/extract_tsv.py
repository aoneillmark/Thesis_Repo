import os
import pandas as pd

# Input TSV file
input_file = "test.tsv"  # Replace with your actual TSV file name

# Output directory
# output_dir = "benchmark_policy"
output_dir = "benchmark_claim"
os.makedirs(output_dir, exist_ok=True)

# Read the TSV file
df = pd.read_csv(input_file, sep="\t")

# Loop through each row and write the policy to a text file
for idx, policy in enumerate(df['claim']):
    file_path = os.path.join(output_dir, f"claim_{idx}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(policy)
    
print(f"Extracted {len(df)} policies into '{output_dir}/'")
