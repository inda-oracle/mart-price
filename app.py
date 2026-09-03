import streamlit as st
import pandas as pd

# 1. 사이트 기본 설정
st.set_page_config(page_title="마트 식자재 가격 검색", layout="wide")

# ==============================================================
# 🚀 [핵심 기술] 외부 유입용 독립 링크(랜딩 페이지) 생성 구역
# ==============================================================
post_id = st.query_params.get("post")

if post_id == "1":
    st.title("🎉 [특가] 이번 주말 삼겹살 반값 대란!")
    st.markdown("**행사 기간:** 2026년 9월 4일(금) ~ 9월 6일(일)")
    st.info("이번 주말, 전국 주요 마트에서 국내산 한돈 삼겹살을 최대 50% 할인합니다. 한정 수량이니 서두르세요!")
    
    # 💡 [지도 링크 추가] 이 부분의 따옴표 안의 주소와 글자를 대표님 마음대로 수정하시면 됩니다!
    st.link_button("🗺️ 내 주변 마트 위치 찾기 (네이버 지도)", "https://map.naver.com")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛒 우리 동네 마트 삼겹살 가격 검색하러 가기", type="primary", use_container_width=True):
        st.query_params.clear() 
        st.rerun()
    st.stop() 

elif post_id == "2":
    st.title("🎪 [장날 정보] 인심 넉넉한 용인 중앙시장 5일장")
    st.markdown("**장날 일정:** 매월 **5일, 10일, 15일, 20일, 25일, 30일**")
    st.info("마트보다 저렴하고 인심 좋은 전통시장! 싱싱한 제철 채소와 갓 짜낸 참기름 등을 구경해 보세요.")
    
    # 💡 [지도 링크 추가] 여기도 마찬가지로 원하는 시장의 카카오맵/네이버 지도 링크를 넣으세요.
    st.link_button("🗺️ 용인 중앙시장 위치 보기 (카카오맵)", "https://map.kakao.com")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 다른 식자재 최저가 검색하러 가기", type="primary", use_container_width=True):
        st.query_params.clear()
        st.rerun()
    st.stop()


# ==============================================================
# 📌 메인 검색 서비스 (파라미터 없이 그냥 접속했을 때 나오는 화면)
# ==============================================================
st.title("🛒 전국 마트 식자재 실시간 가격 검색기")
st.markdown("우리 동네 마트 가격과 전국 최저가를 한눈에 비교해 보세요!")
st.markdown("---")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("adress.zip", encoding='cp949') 
    except:
        df = pd.read_csv("adress.zip", encoding='utf-8')
    
    non_food_keywords = ['치약', '칫솔', '물걸레', '면도', '호일', '가그린', '건전지', '기저귀', '물티슈', '티슈', '로션', '세제', '락스', '비누', '살충제', '에프킬라']
    df = df[~df['상품명'].str.contains('|'.join(non_food_keywords), na=False)]
    
    def categorize(item):
        item = str(item).lower()
        if any(kw in item for kw in ['우유', '치즈', '요거트', '버터', '계란', '달걀']): return '🥛 유제품/계란'
        elif any(kw in item for kw in ['돼지고기', '소고기', '닭', '고등어', '오징어']): return '🥩 정육/수산'
        elif any(kw in item for kw in ['감자', '고구마', '양파', '마늘', '배추', '쌀']): return '🥬 신선 농산물'
        elif any(kw in item for kw in ['라면', '만두', '스파게티', '햇반']): return '🍜 면/간편식'
        else: return '🛒 기타 식자재'
            
    df['카테고리'] = df['상품명'].apply(categorize)
    df['용량'] = df['상품명'].str.extract(r'(?i)([0-9.]+\s*(?:ml|l|g|kg|개|개입|매|캔|팩|봉|인|롤))', expand=False).fillna('단일규격/기타') 
    
    if '주소' in df.columns:
        df['주소'] = df['주소'].fillna("주소 미상")
        df['시도'] = df['주소'].apply(lambda x: str(x).split()[0] if len(str(x).split()) > 0 else '미상')
        df['시군구'] = df['주소'].apply(lambda x: str(x).split()[1] if len(str(x).split()) > 1 else '미상')
        df['표시용_매장명'] = df['판매업소'] + " (" + df['주소'] + ")"
    else:
        df['시도'] = '전체 지역'
        df['시군구'] = '전체 지역'
        df['표시용_매장명'] = df['판매업소']
    
    return df.drop_duplicates(subset=['판매업소', '상품명', '판매가격'])

try:
    df = load_data()
    tab1, tab2 = st.tabs(["🛒 실시간 가격 검색", "📢 할인 행사 & 장날 소식"])
    
    with tab1:
        st.subheader("📍 1. 동네 마트 선택")
        col1, col2, col3 = st.columns(3)
        with col1: selected_sido = st.selectbox("📌 시/도 선택", ["전체"] + sorted(df['시도'].unique().tolist()))
        with col2:
            sigungu_list = ["전체"] if selected_sido == "전체" else ["전체"] + sorted(df[df['시도'] == selected_sido]['시군구'].unique().tolist())
            selected_sigungu = st.selectbox("📌 시/군/구 선택", sigungu_list)
        with col3:
            if selected_sido == "전체": store_list = ["전체"]
            elif selected_sigungu == "전체": store_list = ["전체"] + sorted(df[df['시도'] == selected_sido]['표시용_매장명'].unique().tolist())
            else: store_list = ["전체"] + sorted(df[(df['시도'] == selected_sido) & (df['시군구'] == selected_sigungu)]['표시용_매장명'].unique().tolist())
            selected_store = st.selectbox("🛒 마트 선택", store_list)
    
        if selected_store == "전체":
            clean_store_name, store_address = "전체 매장", "전국 모든 매장" if selected_sido == "전체" else f"{selected_sido} 내 모든 매장"
        else:
            clean_store_name = selected_store.split(" (")[0] if " (" in selected_store else selected_store
            store_address = selected_store.split(" (")[1].replace(")", "") if " (" in selected_store else "주소 미상"
            
        st.info(f"🏪 **선택 매장:** {clean_store_name}  \n📍 **상세 주소:** {store_address}")
        st.divider()

        st.subheader("🔍 2. 상품명 통합 검색")
        global_search_keyword = st.text_input("찾으시는 상품을 입력하세요 (예: 달걀, 삼겹살)", placeholder="검색하시면 마트 가격과 전국 최저가가 동시 분석됩니다.")
        
        if global_search_keyword:
            st.markdown(f"#### 🛒 [{clean_store_name}] '{global_search_keyword}' 판매 가격")
            store_df = df.copy()
            if selected_sido != "전체": store_df = store_df[store_df['시도'] == selected_sido]
            if selected_sigungu != "전체": store_df = store_df[store_df['시군구'] == selected_sigungu]
            if selected_store != "전체": store_df = store_df[store_df['표시용_매장명'] == selected_store]
                
            store_search_df = store_df[store_df['상품명'].str.contains(global_search_keyword, na=False)]
            if len(store_search_df) == 0: st.warning("검색 결과가 없습니다.")
            else:
                display_cols = ['판매업소', '카테고리', '상품명', '판매가격'] if selected_store == "전체" else ['카테고리', '상품명', '판매가격']
                st.caption("💡 표 맨 위의 **'판매가격'**을 누르시면 가장 싼 값부터 자동 정렬됩니다.")
                st.dataframe(store_search_df[display_cols].sort_values(by=['카테고리', '상품명']), use_container_width=True, hide_index=True)

            item_df = df[df['상품명'].str.contains(global_search_keyword, na=False)]
            if len(item_df) > 0:
                st.markdown(f"#### 📊 '{global_search_keyword}' 전국 최저가 분석")
                summary_df = item_df.groupby('용량').agg(전국평균가=('판매가격', 'mean'), 전국최저가=('판매가격', 'min'), 판매지점수=('판매업소', 'count')).reset_index()
                st.dataframe(summary_df.assign(전국평균가=summary_df['전국평균가'].astype(int)), use_container_width=True, hide_index=True)
                
                st.markdown("##### 🏆 특정 브랜드 최저가 매장 찾기")
                exact_product = st.selectbox("🎯 정확한 상품을 선택하세요", sorted(item_df['상품명'].unique()))
                exact_df = item_df[item_df['상품명'] == exact_product]
                
                st.dataframe(exact_df[['상품명', '판매가격', '표시용_매장명']].sort_values(by='판매가격').rename(columns={'표시용_매장명': '판매처'}), use_container_width=True, hide_index=True)
        else:
            st.info("👆 상품명을 검색해 보세요.")

    with tab2:
        st.header("🔥 전국 마트 할인 & 장날 소식")
        st.write("---")
        
        st.subheader("🎉 [특가] 이번 주말 대형마트 삼겹살 반값 할인 대란!")
        st.markdown("전국 주요 마트에서 한돈 삼겹살을 최대 50% 할인합니다.")
        if st.button("👉 자세히 보기 및 삼겹살 가격 비교하기", key="btn_post1"):
            st.query_params["post"] = "1"
            st.rerun()
        
        st.write("---")
        
        st.subheader("🎪 [장날 정보] 인심 넉넉한 용인 중앙시장 5일장 안내")
        st.markdown("매월 5, 10, 15, 20, 25, 30일 개최되는 싱싱한 전통시장.")
        if st.button("👉 자세히 보기 및 시장 채소 가격 비교하기", key="btn_post2"):
            st.query_params["post"] = "2"
            st.rerun()

except Exception as e:
    st.error("데이터 파일을 찾을 수 없습니다.")
