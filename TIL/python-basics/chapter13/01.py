
#sentense에서 3회 이상 등장하는 단어는 무엇일까요? 각 단어와 빈도수를 출력하시오.
# 1. 딕셔너리를 활용해 주세요. 지금까지 배우지 않은 기능 사용하지 말것.
# 2. 가장 간단한 방식으로 처리할 것. 필요할 경우 배우지 않은 개념도 활용.
sentense = "나는 대한민국 서울 구로에서 파이썬 공부를 하고 있습니다." #단어가 100개 이상
words = sentense.split() #type : list

print(type(words))
#나 : Q word를 인덱스로 쪼개서 바구니를 주고 index끼리 비교해서 word의 index안의 값이 =<2 중복된거 출력.  
#gpt: 딕셔너리를 이용하라고 했으니까 word데이터를 딕셔너리에 담아라 단어를 미리 직접 적는 게 아니라, for문이 word를 하나씩 꺼낼 때마다 딕셔너리에 자동으로 넣는 방식으로 가야 해요.

word_count = {} #count를 하면 몇번돌았는지만 확인됨. 
for word in words:
    print(words)
    if word in 