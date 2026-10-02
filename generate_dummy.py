import pandas as pd
import os

# Create dummy Excel data
data = {
    "Name": ["Alice", "Bob", "Charlie"],
    "Email": ["test1@example.com", "test2@example.com", "test3@example.com"],
    "Score": ["95/100", "88/100", "100/100"],
    "Certificate": ["cert_Alice.txt", "cert_Bob.txt", "cert_Charlie.txt"]
}
df = pd.DataFrame(data)
df.to_excel("dummy_data.xlsx", index=False)

# Create dummy attachment files
for name in data["Name"]:
    with open(f"cert_{name}.txt", "w") as f:
        f.write(f"This is a dummy certificate of achievement for {name}!\nGreat job!")

print("Successfully generated dummy_data.xlsx and 3 dummy text files!")
