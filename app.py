import streamlit as st
import pandas as pd

# 1. 사이트 기본 설정
st.set_page_config(page_title="마트 식자재 가격 검색", layout="wide")
st.title("🛒 전국 마트 식자재 실시간 가격 검색기")

# 2. 데이터 불러오기 및 최적화
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("adress.csv", encoding='cp949') 
    except:
        df = pd.read_csv("adress.csv", encoding='utf-8')
    
    # 3. 비식품 강력 필터링
    non_food_keywords = [
        '치약', '칫솔', '물걸레', '면도', '호일', '가그린', '건전지', '기저귀', '물티슈', 
        '티슈', '로션', '립', '세럼', '크림', '선크림', '섬유유연제', '소독', '밴드', 
        '바디워시', '바디밀크', '샴푸', '트리트먼트', '염색', '가스', '패드', '하마', 
        '세제', '장갑', '랩', '지퍼백', '화장지', '생리대', '에어졸', '마스크', '롤백', 
        '종이호일', '락스', '비누', '청소', '유연제', '탈취제', '방향제', '살충제', '모기',
        '제습제', '부탄가스', '위생백', '위생장갑', '에너자이저', 'CAT', 'DOG', '페브리즈', 
        '테크', '액츠', '퍼실', '피죤', '크린백', '자연퐁', '프릴', '트리오', '무균무때', 
        '홈스타', '리스테린', '도브', '드봉', '바디피트', '좋은느낌', '화이트', '닥터지', 
        '디펜드', '라이프리', '키퍼스', '아이!깨끗해', '하기스', '2080', '페리오', '오랄비', 
        '모나리자', '잘풀리는집', '코디', '크리넥스', '타월', '에프킬라'
    ]
    df = df[~df['상품명'].str.contains('|'.join(non_food_keywords), na=False)]
    
    # 4. 식자재 카테고리
    def categorize(item):
        item = str(item).lower()
        if any(kw in item for kw in ['우유', '치즈', '요거트', '요플레', '불가리스', '이오', '버터', '마가린', '계란', '달걀', '유정란', '목초란']): 
            return '🥛 03. 유제품/계란/버터'
        elif any(kw in item for kw in ['돼지고기', '쇠고기', '소고기', '닭', '오리', '고등어', '오징어', '갈치', '조기', '새우', '연어']): 
            return '🥩 01. 정육/수산물'
        elif any(kw in item for kw in ['감자', '고구마', '깻잎', '당근', '대파', '파', '마늘', '무', '배추', '버섯', '상추', '시금치', '양배추', '양파', '오이', '쪽파', '고추', '애호박', '콩나물', '쌀', '현미', '참깨', '채소', '두부', '진미', '진상미']): 
            return '🥬 02. 신선 농산물 (채소/곡물)'
        elif any(kw in item for kw in ['햄', '베이컨', '소시지', '비엔나', '후랑크', '스팸', '어묵', '맛살', '크래미', '참치', '젓', '명란']): 
            return '🥫 04. 가공육/가공수산물'
        elif any(kw in item for kw in ['라면', '소면', '당면', '냉면', '스파게티', '우동', '국수', '파스타', '만두', '교자', '너구리', '안성탕면', '왕뚜껑']): 
            return '🍜 05. 면/만두류'
        elif any(kw in item for kw in ['떡볶이', '볶음밥', '컵밥', '덮밥', '국밥', '짜장', '카레', '스프', '죽', '초밥', '돈까스', '돈카츠', '핫도그', '치킨', '너겟', '곰탕', '육개장', '미역국', '햇반', '오뚜기밥']): 
            return '🥣 06. 간편식/즉석식품'
        elif any(kw in item for kw in ['간장', '고추장', '된장', '쌈장', '토장', '와사비', '케찹', '마요네즈', '식초', '드레싱', '식용유', '카놀라유', '포도씨유', '콩기름', '참기름', '들기름', '액젓', '다시다', '맛선생', '소금', '설탕', '물엿', '올리고당', '벌꿀', '고춧가루', '잼']): 
            return '🧂 07. 소스/조미료/오일'
        elif any(kw in item for kw in ['과자', '스낵', '크래커', '쿠키', '초코', '카카오', '가나', '오예스', '젤리', '캔디', '후르트텔라', '자유시간', '에너지바', '식빵', '롤', '만쥬', '호떡', '빵', '보름달', '아이스크림', '돼지바', '메로나', '바밤바', '월드콘', '싸만코', '투게더', '부라보콘', '아몬드', '땅콩', '콘푸로스트', '콘푸라이트', '스페셜K', '유과', '약과', '마이구미', '아이비']): 
            return '🍪 08. 간식/빵/빙과류'
        elif any(kw in item for kw in ['생수', '삼다수', '아이시스', '콜라', '사이다', '탄산수', '스프라이트', '게토레이', '파워에이드', '포카리스웨트', '오렌지', '커피', '콜드브루', '차', '믹스', '라떼', '아메리카노', '블렌드', '모카골드', '로스트', '티백', '막걸리', '맥주', '소주', '에일', '카스', '테라', '하이트', '참이슬', '처음처럼', '우국생', '프로틴', '베지밀', '두유', '헛개', '레드불', '에너지', '핫식스', '박카스', '비타', '오로나민', '깨수깡', '여명']): 
            return '☕ 09. 음료/주류/커피'
        elif any(kw in item for kw in ['이유식', '분유', '명작', '드림', '진밥', '퓨레', '김치', '단무지', '황도', '파인애플', '미역', '밀가루', '부침가루', '튀김가루', '김']): 
            return '🛒 10. 식재료/유아식/기타'
        else: 
            return '🛒 10. 기타 식자재'
            
    df['카테고리'] = df['상품명'].apply(categorize)
    df['용량'] = df['상품명'].str.extract(r'(?i)([0-9.]+\s*(?:ml|l|g|kg|개|개입|매|캔|팩|봉|인|롤))', expand=False)
    df['용량'] = df['용량'].fillna('단일규격/기타') 
    
    if '주소' in df.columns:
        df['주소'] = df['주소'].fillna("주소 미상")
        df['시도'] = df['주소'].apply(lambda x: str(x).split()[0] if len(str(x).split()) > 0 else '미상')
        df['시군구'] = df['주소'].apply(lambda x: str(x).split()[1] if len(str(x).split()) > 1 else '미상')
        df['표시용_매장명'] = df['판매업소'] + " (" + df['주소'] + ")"
    else:
        df['시도'] = '전체 지역'
        df['시군구'] = '전체 지역'
        df['표시용_매장명'] = df['판매업소']
    
    df = df.drop_duplicates(subset=['판매업소', '상품명', '판매가격'])
    return df

try:
    df = load_data()
    
    tab1, tab2 = st.tabs(["🏪 지역별 마트 지점 검색", "🔍 상품명으로 전국 최저가 찾기"])
    
    with tab1:
        st.subheader("1. 지역 및 마트를 순서대로 선택하세요")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sido_list = sorted(df['시도'].unique())
            selected_sido = st.selectbox("📌 1. 시/도 선택", sido_list)
        with col2:
            sigungu_list = sorted(df[df['시도'] == selected_sido]['시군구'].unique())
            selected_sigungu = st.selectbox("📌 2. 시/군/구 선택", sigungu_list)
        with col3:
            store_list = sorted(df[(df['시도'] == selected_sido) & (df['시군구'] == selected_sigungu)]['표시용_매장명'].unique())
            selected_store = st.selectbox("🛒 3. 마트 선택", store_list)
        
        st.write("---")
        
        if " (" in selected_store:
            clean_store_name = selected_store.split(" (")[0]
            store_address = selected_store.split(" (")[1].replace(")", "")
        else:
            clean_store_name = selected_store
            store_address = "주소 미상"
            
        # 💡 [정렬 개선] 마트명과 주소를 깔끔한 수직 구조로 정돈된 마크다운 상자에 표시
        st.markdown(f"""
        <div style="padding: 15px; border-radius: 8px; background-color: #f0f2f6; border-left: 5px solid #ff4b4b; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 16px; font-weight: bold; color: #111;">🏪 선택 매장: {clean_store_name}</p>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #555;">📍 상세 주소: {store_address}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader(f"[{clean_store_name}] 취급 상품 및 가격")
        search_keyword_1 = st.text_input("찾으시는 상품 이름을 입력하세요 (예: 달걀, 삼겹살)", key="search1")
        
        store_df = df[df['표시용_매장명'] == selected_store]
        if search_keyword_1:
            store_df = store_df[store_df['상품명'].str.contains(search_keyword_1, na=False)]
        
        if len(store_df) == 0:
            st.warning(f"해당 지점에는 검색하신 상품이 없습니다.")
        else:
            display_df = store_df[['카테고리', '상품명', '판매가격']].sort_values(by=['카테고리', '상품명'])
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("해당 상품의 용량별 전체 물가 및 특정 제품 최저가 찾기")
        search_keyword_2 = st.text_input("찾으시는 상품 이름을 입력하세요 (예: 우유, 라면)", key="search2")
        
        if search_keyword_2:
            item_df = df[df['상품명'].str.contains(search_keyword_2, na=False)]
            
            if len(item_df) == 0:
                st.warning(f"'{search_keyword_2}'(으)로 검색된 상품이 없습니다.")
            else:
                summary_df = item_df.groupby('용량').agg(
                    전국평균가=('판매가격', 'mean'),
                    전국최저가=('판매가격', 'min'),
                    전국최고가=('판매가격', 'max'),
                    포함된브랜드수=('상품명', 'nunique'),
                    판매지점수=('판매업소', 'count')
                ).reset_index()
                
                summary_df['전국평균가'] = summary_df['전국평균가'].astype(int)
                summary_df = summary_df.sort_values(by='용량')
                
                st.markdown(f"##### 📊 '{search_keyword_2}' 용량별 전국 물가 요약")
                st.success("💡 제조사와 상관없이 **동일한 용량(중량)**을 가진 상품들의 전체 평균 가격입니다.")
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                st.divider()
                
                st.markdown("##### 🛒 특정 상품의 브랜드별 최저가 지점 찾기")
                matched_products = sorted(item_df['상품명'].unique())
                exact_product = st.selectbox("🎯 정확한 상품(브랜드+용량)을 선택하세요", matched_products)
                
                exact_df = item_df[item_df['상품명'] == exact_product]
                
                avg_price = int(exact_df['판매가격'].mean())
                min_price = int(exact_df['판매가격'].min())
                max_price = int(exact_df['판매가격'].max())
                
                st.markdown(f"**[{exact_product}] 전국 물가 요약**")
                col1, col2, col3 = st.columns(3)
                col1.metric("전국 평균가", f"{avg_price:,} 원")
                col2.metric("전국 최저가", f"{min_price:,} 원")
                col3.metric("전국 최고가", f"{max_price:,} 원")
                
                display_item_df = exact_df[['상품명', '판매가격', '표시용_매장명']].sort_values(by=['판매가격', '표시용_매장명'])
                display_item_df = display_item_df.rename(columns={'표시용_매장명': '판매처(주소)'})
                st.dataframe(display_item_df, use_container_width=True, hide_index=True)
        else:
            st.info("검색창에 상품명을 입력하시면, 상단에는 용량별 평균이, 하단에는 개별 제품의 최저가 정보가 나타납니다.")

except Exception as e:
    st.error("데이터 파일을 찾을 수 없습니다. 'adress.csv' 파일을 서버에 업로드해 주세요.")
