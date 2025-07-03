import sys
sys.path.append('src')
from database import calculate_prize_distribution

participants = 100
fee = 10

print("=== PYRAMID vs NON-LINEAR ===")
print(f"Тест: {participants} участников, ${fee} взнос\n")

# Pyramid
result_pyramid = calculate_prize_distribution(participants, fee, 'pyramid')
print("🏆 PYRAMID:")
for i, prize in enumerate(result_pyramid['distribution'][:5]):
    print(f"{prize['place']} место: ${prize['amount']} ({prize['percentage']}%)")

print()

# Non-linear  
result_nonlinear = calculate_prize_distribution(participants, fee, 'nonlinear')
print("📊 NON-LINEAR:")
for i, prize in enumerate(result_nonlinear['distribution'][:5]):
    print(f"{prize['place']} место: ${prize['amount']} ({prize['percentage']}%)")