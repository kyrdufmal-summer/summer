
total_minutes = 125
hours = total_minutes // 60
minutes = total_minutes % 60

print(hours, "시간")
print(minutes, "분")
print(hours,"시간")

# #MISSION 01 — 구매 금액 계산 프로그램
# 1. 상품 금액을 계산합니다.
# 2. 배송비를 더한 최종 금액을 계산합니다.
# 3. 결과를 각각 출력합니다.

price = 18000      #가격
quantity = 3       #수량
shpping_fee = 3000   #배송비

product_Price = price*quantity
total_price = product_Price + shpping_fee

print(f"총 상품 금액 :{product_Price:,}")
print(f"배송비:{shpping_fee:,}원")
print(f"최종금액:{total_price:,}원")

#MISSION 02 — 시간을 시간과 분으로 바꾸기
# 총 학습 시간이 250분이라고 가정합니다.
# 다음 결과를 출력하세요.
# • //를 한 번 사용
# • %를 한 번 사용
# • 결과를 변수에 저장
# • 실행 전에 값을 직접 계산해 예상
total_study_time = 250
hours = total_study_time//60
minutes = total_study_time%60
print(f"{hours}시 {minutes}분")

#14. 과제 — 나의 생활 계산기 만들기

# 과제 A. 카페 주문 금액
# 커피 4,500원 × 3잔
# 케이크 6,500원 × 2개
# 총 금액을 계산합니다.
coffee = 4500*3
cake = 6500*2
total_price = coffee + cake
print(f"총 금액은 {total_price:,}입니다.")

# 과제 B. 학습 시간 변환
# 총 385분을 시간과 분으로 바꿉니다.
hours = 385 // 60
minutes = 385 % 60
print(f"385분의 시간은 {hours}시간, {minutes}분 입니다.")

# 과제 C. 직사각형 계산
# • 넓이를 계산
# • 넓이가 100보다 큰지 비교
# • width += 3 적용
# • 새 넓이를 다시 계산
width = 12
height = 8

rect_area = width * height
if 100 <rect_area:
    print("직사각형의 넓이는 100보다 큽니다.")
else:    
    print("직사각형의 넓이는 100보다 작습니다.")
width +=3
rect_area = width * height
print(f"new 직사각형의 넓이는 {rect_area} 입니다.")