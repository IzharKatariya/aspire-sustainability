from app.validation.validator import _extract_numbers

# Simulate text containing a GRI code reference
text = (
    "In accordance with GRI 306-2 and GRI 306-3, the company generated "
    "185,000 tonnes of waste, of which 92,500 tonnes were recycled."
)
numbers = _extract_numbers(text)
print("Extracted numbers (should only see 185000 and 92500):")
for val, raw, ctx in numbers:
    print(f"  {raw} -> {val}")

    