import sys
import os
sys.path.append('src')

from database import calculate_prize_distribution

def test_participants(count, fee):
    print(f"\n=== ТЕСТ: {count} участников, ${fee} взнос ===")
    result = calculate_prize_distribution(count, fee, 'pyramid')
    
    print(f"Общий фонд: ${result['total_pool']}")
    print(f"Наша комиссия: ${result['our_commission']}")
    print(f"Призовой фонд: ${result['prize_pool']}")
    print(f"Призовых мест: {result['prize_places']} ({result['prize_places']/count*100:.0f}% от участников)")
    
    print("\nРаспределение призов:")
    total_distributed = 0
    for prize in result['distribution']:
        print(f"{prize['place']} место: ${prize['amount']} ({prize['percentage']:.1f}%)")
        total_distributed += prize['amount']
    
    print(f"\nВсего распределено: ${total_distributed:.2f}")
    print(f"Остаток: ${result['prize_pool'] - total_distributed:.2f}")

# Тестируем разные количества
test_participants(100, 10)  # 20 призовых мест
test_participants(50, 20)   # 10 призовых мест  
test_participants(25,10)   # 5 призовых мест
test_participants(10, 100)  # 2 призовых места