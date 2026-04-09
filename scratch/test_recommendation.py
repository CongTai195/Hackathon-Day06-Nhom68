import json
from tools import recommend_cars

def test_recommendation_700m():
    print("Testing recommendation for 700M...")
    result = recommend_cars.invoke({"budget_million_vnd": 700, "seats_needed": 5, "use_case": "thành phố"})
    print(result)
    
    # Expecting VF e34 and VF 6
    assert "VF e34" in result or "VF 6" in result
    assert "VF 3" not in result # Should not recommend mini car for 700M budget

def test_recommendation_long_range():
    print("\nTesting recommendation for 1200M, long distance...")
    result = recommend_cars.invoke({"budget_million_vnd": 1200, "seats_needed": 5, "use_case": "đường dài"})
    print(result)

if __name__ == "__main__":
    test_recommendation_700m()
    test_recommendation_long_range()
