import streamlit as st
import pandas as pd
import random
import altair as alt
import re 
from collections import Counter

# 🚀 Supabase 연결용 라이브러리
from supabase import create_client, Client

# 1. 사이트 기본 설정
st.set_page_config(page_title="마트 식자재 가격 검색", layout="wide")

# ==============================================================
# 👑 사이드바: 숨겨진 관리자 로그인 모드
# ==============================================================
with st.sidebar:
    st.markdown("### 🛠️ 관리자 전용 메뉴")
    admin_input = st.text_input("관리자 암호를 입력하세요", type="password")
    is_admin = (admin_input == "0000") 
    
    if is_admin:
        st.success("✅ 관리자 권한 활성화됨")
        st.info("이제 유저들의 모든 글을 강제 삭제할 수 있으며, 공지사항을 등록할 수 있습니다.")

# ==============================================================
# 🗄️ Supabase 데이터베이스 연결 세팅
# ==============================================================
SUPABASE_URL = "https://rptvjenmizzvsnugeczf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJwdHZqZW5taXp6dnNudWdlY3pmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg4NDIxMDEsImV4cCI6MjEwNDQxODEwMX0.GcKYTDFV-DXUFz_Oe34EpiYldGRqxB7pK9n74bJQJNI"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()


# ==============================================================
# 🚀 외부 유입용 독립 링크(랜딩 페이지) 생성 구역
# ==============================================================
post_id = st.query_params.get("post")

if post_id == "1":
    st.title("🎉 [특가] 이번 주말 삼겹살 반값 대란!")
    st.markdown("**행사 기간:** 2026년 9월 4일(금) ~ 9월 6일(일)")
    st.info("이번 주말, 전국 주요 마트에서 국내산 한돈 삼겹살을 최대 50% 할인합니다. 한정 수량이니 서두르세요!")
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
    st.link_button("🗺️ 용인 중앙시장 위치 보기 (카카오맵)", "https://map.kakao.com")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 다른 식자재 최저가 검색하러 가기", type="primary", use_container_width=True):
        st.query_params.clear()
        st.rerun()
    st.stop()


# ==============================================================
# 📌 메인 검색 서비스
# ==============================================================
st.title("🛒 전국 마트 식자재 실시간 가격 검색기")
st.markdown("우리 동네 마트 가격과 전국 최저가를 한눈에 비교해 보세요!")
st.markdown("---")

# ⚡ [극한 최적화 구간] 연산 단순화 및 타입 지정
@st.cache_data
def load_data():
    try:
        # csv 읽을 때 필요한 열만 읽거나 타입을 지정하면 더 빠르지만, 범용성을 위해 일단 유지
        df = pd.read_csv("adress.zip", encoding='cp949') 
    except:
        df = pd.read_csv("adress.zip", encoding='utf-8')
    
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
        '모나리자', '잘풀리는집', '코디', '크리넥스', '타월', '에프킬라', '다우니', '샤프란', '리큐'
    ]
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
        # split을 여러 번 호출하는 대신 정규식이나 한번의 split으로 개선
        addr_split = df['주소'].str.split(n=2, expand=True)
        df['시도'] = addr_split[0].fillna('미상')
        df['시군구'] = addr_split[1].fillna('미상')
        df['표시용_매장명'] = df['판매업소'] + " (" + df['주소'] + ")"
    else:
        df['시도'] = '전체 지역'
        df['시군구'] = '전체 지역'
        df['표시용_매장명'] = df['판매업소']
    
    df = df.drop_duplicates(subset=['판매업소', '상품명', '판매가격'])
    food_only_df = df[df['카테고리'] != '🛒 기타 식자재']
    
    date_col = next((c for c in df.columns if c in ['날짜', '조사일', '조사일자', 'date', 'Date']), None)
    weather_info = {}
    
    if date_col and len(df[date_col].unique()) > 1:
        dates = sorted(df[date_col].unique())
        past_date, curr_date = dates[0], dates[-1]
        
        past_df = food_only_df[food_only_df[date_col] == past_date].groupby('상품명')['판매가격'].mean().reset_index(name='past_price')
        curr_df = food_only_df[food_only_df[date_col] == curr_date].groupby('상품명')['판매가격'].mean().reset_index(name='curr_price')
        diff_df = pd.merge(past_df, curr_df, on='상품명')
        diff_df['drop_rate'] = ((diff_df['past_price'] - diff_df['curr_price']) / diff_df['past_price']) * 100
        
        drops = diff_df[diff_df['drop_rate'] > 0]
        if not drops.empty:
            best_item = drops.sample(1).iloc[0]
            weather_info['msg'] = f"희소식입니다! <b>[{best_item['상품명']}]</b>의 전국 평균 가격이 지난번 조사 대비 <b>약 {int(best_item['drop_rate'])}% 떨어졌습니다.</b> 지금 우리 동네 마트 가격을 검색해 알뜰하게 구매해 보세요!"
            weather_info['price1'] = int(best_item['past_price'])
            weather_info['price2'] = int(best_item['curr_price'])
            weather_info['label1'] = f"과거 평균가|({past_date})"
            weather_info['label2'] = f"현재 평균가|({curr_date})"
        else:
            item_name = random.choice(food_only_df['상품명'].unique())
            weather_info['price1'] = int(food_only_df[food_only_df['상품명']==item_name]['판매가격'].mean() * 1.1)
            weather_info['price2'] = int(food_only_df[food_only_df['상품명']==item_name]['판매가격'].mean())
            weather_info['msg'] = f"오늘의 장바구니 픽! <b>[{item_name}]</b> 전국 평균 가격 변동을 확인해 보세요."
            weather_info['label1'] = "과거 평균가|(이전)"
            weather_info['label2'] = "현재 평균가|(최근)"
    else:
        summary = food_only_df.groupby('상품명')['판매가격'].mean().reset_index(name='curr_avg')
        best_item = summary.sample(1).iloc[0]
        fake_drop = random.randint(15, 30)
        
        weather_info['price2'] = int(best_item['curr_avg'])
        weather_info['price1'] = int(weather_info['price2'] / (1 - fake_drop/100))
        weather_info['msg'] = f"오늘의 물가 소식! <b>[{best_item['상품명']}]</b> 전국 평균 가격이 <b>약 {fake_drop}% 하락</b>하는 추세입니다. (※ 현재는 데모 화면이며, 과거 날짜의 엑셀 데이터가 추가되면 실제 하락폭이 자동 계산됩니다.)"
        weather_info['label1'] = "과거 평균가|(가상 데이터)"
        weather_info['label2'] = "현재 평균가|(실제 데이터)"
        
    return df, food_only_df, weather_info

try:
    df, food_only_df, weather_info = load_data()
    
    tab1, tab2, tab3 = st.tabs(["🔍 1. 실시간 가격 검색", "💬 2. 핫딜 & 동네 소통방", "🎯 3. 장보기 전 목표가 판독기"])
    
    with tab1:
        with st.container(border=True):
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #fffbc8 0%, #ffeedb 100%); border: 1px solid #ffeeba; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                <h4 style="margin: 0 0 10px 0; color: #d39e00;">💡 오늘의 물가 기상도</h4>
                <p style="margin: 0; font-size: 15px; color: #333; line-height: 1.5;">{weather_info['msg']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            c_df = pd.DataFrame({"구분": [weather_info['label1'], weather_info['label2']], "가격": [weather_info['price1'], weather_info['price2']]})
            
            c_chart = alt.Chart(c_df).mark_bar(size=60).encode(
                x=alt.X('구분:N', title='', sort=[weather_info['label1'], weather_info['label2']], axis=alt.Axis(
                    labelAngle=0, 
                    labelFontWeight='bold',
                    labelExpr="split(datum.value, '|')" 
                )),
                y=alt.Y('가격:Q', title='평균 금액 (원)', axis=alt.Axis(labels=False, ticks=False)),
                color=alt.condition(alt.datum.구분 == weather_info['label2'], alt.value('#03c75a'), alt.value('#b0b8c1'))
            ).properties(height=250)
            
            c_text = c_chart.mark_text(align='center', baseline='bottom', dy=-5, fontWeight='bold', fontSize=14).encode(
                text=alt.Text('가격:Q', format=',d')
            )
            
            st.altair_chart(c_chart + c_text, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("📍 1. 동네 마트 선택")
        col1, col2, col3 = st.columns(3)
        
        # 💡 list() 변환 과정을 최소화하여 렌더링 속도 향상
        sido_options = ["전체"] + sorted(df['시도'].unique())
        with col1: 
            selected_sido = st.selectbox("📌 시/도 선택", sido_options)
        
        with col2:
            if selected_sido == "전체":
                sigungu_options = ["전체"]
            else:
                sigungu_options = ["전체"] + sorted(df.loc[df['시도'] == selected_sido, '시군구'].unique())
            selected_sigungu = st.selectbox("📌 시/군/구 선택", sigungu_options)
            
        with col3:
            if selected_sido == "전체": 
                store_options = ["전체"]
            elif selected_sigungu == "전체": 
                store_options = ["전체"] + sorted(df.loc[df['시도'] == selected_sido, '표시용_매장명'].unique())
            else: 
                store_options = ["전체"] + sorted(df.loc[(df['시도'] == selected_sido) & (df['시군구'] == selected_sigungu), '표시용_매장명'].unique())
            selected_store = st.selectbox("🛒 마트 선택", store_options)
    
        if selected_store == "전체":
            clean_store_name, store_address = "전체 매장", "전국 모든 매장" if selected_sido == "전체" else f"{selected_sido} 내 모든 매장"
            st.markdown(f"""
            <div style="padding: 15px; border-radius: 8px; background-color: #e8f0fe; border-left: 5px solid #ff4b4b; margin: 10px 0 20px 0;">
                <p style="margin: 0; font-size: 16px; font-weight: bold; color: #111;">🏪 선택 구역: {clean_store_name}</p>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: #555;">📍 안내: {store_address}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            clean_store_name = selected_store.split(" (")[0] if " (" in selected_store else selected_store
            store_address = selected_store.split(" (")[1].replace(")", "") if " (" in selected_store else "주소 미상"
            map_url = f"https://map.naver.com/v5/search/{clean_store_name}"
            
            st.markdown(f"""
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; padding: 15px; border-radius: 8px; background-color: #e8f0fe; border-left: 5px solid #ff4b4b; margin: 10px 0 20px 0; gap: 15px;">
                <div>
                    <p style="margin: 0; font-size: 16px; font-weight: bold; color: #111;">🏪 선택 매장: {clean_store_name}</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #555;">📍 상세 주소: {store_address}</p>
                </div>
                <a href="{map_url}" target="_blank" style="background-color: #03c75a; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">🗺️ 네이버 지도</a>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.subheader("🔍 2. 상품명 통합 검색")
        
        global_search_keyword = st.text_input("찾으시는 상품을 입력하세요 (예: 우유, 삼겹살)", placeholder="검색하시면 전국 마트 가격과 동시 분석됩니다.")
        
        if global_search_keyword:
            # boolean indexing 최적화
            base_mask = df['상품명'].str.contains(global_search_keyword, na=False)
            base_item_df = df[base_mask]
            
            if base_item_df.empty: 
                st.warning("전국 매장에 검색하신 조건의 상품이 없습니다.")
            else:
                word_counter = Counter()
                for name in base_item_df['상품명'].unique():
                    words = re.findall(r'[가-힣a-zA-Z]+', name)
                    for w in words:
                        if w != global_search_keyword and len(w) > 1:
                            word_counter[w] += 1
                
                top_words = [w for w, count in word_counter.most_common(12)]
                exclude_keywords = []
                
                if top_words:
                    with st.expander("🚫 원하지 않는 상품이 섞여 있나요? (제외할 단어를 체크하세요)", expanded=True):
                        cols = st.columns(6)
                        for i, w in enumerate(top_words):
                            if cols[i % 6].checkbox(w, key=f"exc_{w}"):
                                exclude_keywords.append(w)
                
                # df.copy() 대신 뷰(View)를 활용하거나 조건 마스크를 먼저 만들어 메모리 복사 방지
                store_mask = base_mask.copy()
                
                if selected_sido != "전체": 
                    store_mask &= (df['시도'] == selected_sido)
                if selected_sigungu != "전체": 
                    store_mask &= (df['시군구'] == selected_sigungu)
                if selected_store != "전체": 
                    store_mask &= (df['표시용_매장명'] == selected_store)
                    
                for ex in exclude_keywords:
                    ex_mask = df['상품명'].str.contains(ex, na=False)
                    store_mask &= ~ex_mask
                    base_mask &= ~ex_mask
                        
                store_search_df = df[store_mask]
                
                st.markdown(f"#### 🛒 [{clean_store_name}] '{global_search_keyword}' 판매 가격")
                if store_search_df.empty: 
                    st.warning("해당 매장에는 검색/제외 조건에 맞는 상품이 없습니다.")
                else:
                    display_cols = ['판매업소', '카테고리', '상품명', '판매가격'] if selected_store == "전체" else ['카테고리', '상품명', '판매가격']
                    # .loc를 사용하여 안전하게 컬럼 선택 후 복사
                    display_df = store_search_df.loc[:, display_cols].sort_values(by=['판매가격', '상품명'])
                    display_df['판매가격'] = display_df['판매가격'].apply(lambda x: f"{int(x):,} 원")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                item_df = df[base_mask]
                
                if not item_df.empty:
                    st.markdown(f"#### 📊 '{global_search_keyword}' 전국 최저/최고가 분석")
                    
                    summary_df = item_df.groupby(['상품명', '용량']).agg(
                        전국평균가=('판매가격', 'mean'), 
                        전국최저가=('판매가격', 'min'), 
                        전국최고가=('판매가격', 'max'), 
                        판매지점수=('판매업소', 'count')
                    ).reset_index()
                    
                    summary_df = summary_df.sort_values(by=['상품명', '용량']).reset_index(drop=True)
                    summary_df.insert(0, '차트 번호', [f"{i}번" for i in range(1, len(summary_df) + 1)])
                    
                    st.markdown("##### 📈 상품별 전국 가격 비교 차트")
                    
                    chart_data = summary_df[['차트 번호', '상품명', '용량', '전국최저가', '전국평균가', '전국최고가']].melt(id_vars=['차트 번호', '상품명', '용량'], var_name='구분', value_name='가격')
                    
                    main_chart = alt.Chart(chart_data).mark_bar().encode(
                        x=alt.X('차트 번호:N', title='상품 번호 (아래 데이터 요약표 참고)', sort=summary_df['차트 번호'].tolist(), axis=alt.Axis(labelAngle=0)),
                        xOffset='구분:N',
                        y=alt.Y('가격:Q', title='가격 (원)'),
                        color=alt.Color('구분:N', title='가격 종류', scale=alt.Scale(domain=['전국최저가', '전국평균가', '전국최고가'], range=['#03c75a', '#ffc107', '#ff4b4b'])),
                        tooltip=['차트 번호', '상품명', '용량', '구분', alt.Tooltip('가격', format=',')] 
                    ).properties(height=350)
                    
                    st.altair_chart(main_chart, use_container_width=True)
                    
                    display_summary_df = summary_df.copy()
                    display_summary_df['전국평균가'] = display_summary_df['전국평균가'].apply(lambda x: f"{int(x):,} 원")
                    display_summary_df['전국최저가'] = display_summary_df['전국최저가'].apply(lambda x: f"{int(x):,} 원")
                    display_summary_df['전국최고가'] = display_summary_df['전국최고가'].apply(lambda x: f"{int(x):,} 원")
                    display_summary_df['판매지점수'] = display_summary_df['판매지점수'].apply(lambda x: f"{int(x):,} 곳")
                    
                    st.markdown("##### 📝 데이터 요약표 (차트 번호와 완벽히 매칭됩니다)")
                    st.dataframe(display_summary_df, use_container_width=True, hide_index=True)
                    
                    st.markdown("##### 🏆 특정 브랜드 최저가 매장 찾기")
                    exact_product = st.selectbox("🎯 정확한 상품을 선택하세요", sorted(item_df['상품명'].unique()))
                    exact_df = item_df[item_df['상품명'] == exact_product]
                    
                    display_item_df = exact_df[['상품명', '판매가격', '표시용_매장명']].sort_values(by='판매가격')
                    display_item_df = display_item_df.rename(columns={'표시용_매장명': '판매처'})
                    display_item_df['판매가격'] = display_item_df['판매가격'].apply(lambda x: f"{int(x):,} 원")
                    
                    display_item_df['지도보기'] = display_item_df['판매처'].apply(
                        lambda x: f"https://map.naver.com/v5/search/{x.split(' (')[0]}"
                    )
                    
                    st.dataframe(
                        display_item_df,
                        column_config={
                            "지도보기": st.column_config.LinkColumn("🗺️ 매장 위치", display_text="[ 📍 지도 열기 ]")
                        },
                        use_container_width=True, 
                        hide_index=True
                    )
        
        else:
            if selected_store != "전체":
                st.markdown(f"#### 📦 [{clean_store_name}] 전체 취급 품목")
                store_df = df.loc[df['표시용_매장명'] == selected_store, ['카테고리', '상품명', '판매가격']]
                display_df = store_df.sort_values(by=['카테고리', '상품명'])
                display_df['판매가격'] = display_df['판매가격'].apply(lambda x: f"{int(x):,} 원")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("👆 상품명을 검색하시거나, 지역 마트를 구체적으로 선택해 보세요.")

    # ==============================================================
    # 💬 2. 핫딜 & 동네 소통방 
    # ==============================================================
    with tab2:
        st.subheader("📢 [이벤트] 진행 중인 기획전")
        with st.container(border=True):
            st.markdown("##### 🎉 [특가] 이번 주말 대형마트 삼겹살 반값 할인 대란!")
            if st.button("👉 자세히 보기 및 삼겹살 가격 비교하기", key="btn_post1"):
                st.query_params["post"] = "1"
                st.rerun()
            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
            st.markdown("##### 🎪 [장날 정보] 인심 넉넉한 용인 중앙시장 5일장 안내")
            if st.button("👉 자세히 보기 및 시장 채소 가격 비교하기", key="btn_post2"):
                st.query_params["post"] = "2"
                st.rerun()
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.subheader("💬 우리 동네 실시간 소통방 (공지 및 꿀팁)")
        
        if is_admin:
            with st.expander("🚨 [관리자 전용] 새 공지사항 작성하기", expanded=True):
                with st.form("admin_notice_form"):
                    notice_title = st.text_input("공지 제목 (작성자 이름으로 표시됨)", value="🚨 운영자 알림")
                    notice_msg = st.text_area("공지 내용")
                    if st.form_submit_button("공지사항 등록", type="primary"):
                        supabase.table("community_posts").insert({
                            "nickname": notice_title,
                            "location": "공지사항", 
                            "content": notice_msg,
                            "password": "admin"
                        }).execute()
                        st.success("공지가 등록되었습니다.")
                        st.rerun()

        try:
            response = supabase.table("community_posts").select("*").order("created_at", desc=True).limit(50).execute()
            posts = response.data
            
            notice_posts = [p for p in posts if p.get('location') == '공지사항']
            user_posts = [p for p in posts if p.get('location') != '공지사항']

            if notice_posts:
                for post in notice_posts:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 5px solid #ffc107; margin-bottom: 5px;">
                        <span style="font-size: 15px; font-weight: bold; color: #856404;">{post['nickname']}</span><br>
                        <p style="margin: 8px 0 0 0; font-size: 15px; color: #333;">{post['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if is_admin:
                        if st.button("🗑️ 이 공지 내리기", key=f"del_n_{post['id']}"):
                            supabase.table("community_posts").delete().eq("id", post['id']).execute()
                            st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)

            if not user_posts:
                st.info("아직 등록된 동네 꿀팁이 없습니다. 첫 번째 꿀팁을 남겨주세요!")
            else:
                for post in user_posts:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 8px; background-color: #f0f4f8; border-left: 5px solid #007bff; margin-bottom: 5px;">
                        <span style="font-size: 15px; font-weight: bold; color: #111;">👤 {post['nickname']}</span> 
                        <span style="font-size: 13px; color: #6c757d;">(📍 {post['location']})</span><br>
                        <p style="margin: 8px 0 0 0; font-size: 15px; color: #333;">{post['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if is_admin:
                        if st.button("🚨 관리자 강제 삭제", key=f"admin_del_{post['id']}"):
                            supabase.table("community_posts").delete().eq("id", post['id']).execute()
                            st.rerun()
                    else:
                        with st.expander("🗑️ 이 글 삭제하기"):
                            d_col1, d_col2 = st.columns([3, 1])
                            with d_col1:
                                del_pw = st.text_input("글 작성시 입력한 비밀번호", type="password", key=f"pw_{post['id']}", label_visibility="collapsed")
                            with d_col2:
                                if st.button("삭제", key=f"del_{post['id']}", use_container_width=True):
                                    saved_pw = post.get('password')
                                    if saved_pw and del_pw == str(saved_pw):
                                        supabase.table("community_posts").delete().eq("id", post['id']).execute()
                                        st.rerun()
                                    elif not saved_pw:
                                        st.error("비밀번호가 설정되지 않은 과거 글이라 관리자만 지울 수 있습니다.")
                                    else:
                                        st.error("비밀번호가 일치하지 않습니다.")
                    st.markdown("<br>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"서버에서 게시글을 불러오는 중 문제가 발생했습니다. ({e})")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        st.markdown("##### ✍️ 나도 실시간 꿀팁 남기기")
        with st.form("community_post"):
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                user_name = st.text_input("닉네임", placeholder="예: 광명알뜰맘")
            with col_info2:
                user_loc = st.text_input("동네 마트 위치", placeholder="예: 미금역 농협하나로마트")
            with col_info3:
                user_pw = st.text_input("비밀번호 (글 삭제용)", type="password", placeholder="숫자 4자리")
                
            user_msg = st.text_area("어떤 세일 정보가 있나요?", placeholder="예: 방금 갔는데 시금치 한 단에 1000원 떨이 중이에요! 수량 5개 남음!")
            
            submitted = st.form_submit_button("📢 동네 사람들에게 공유하기", type="primary", use_container_width=True)
            if submitted:
                if user_name and user_msg and user_loc and user_pw:
                    try:
                        supabase.table("community_posts").insert({
                            "nickname": user_name,
                            "location": user_loc,
                            "content": user_msg,
                            "password": user_pw
                        }).execute()
                        st.success("소중한 꿀팁 감사합니다! 실시간 목록에 반영되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error("🚨 저장 실패! Supabase에서 'password' 칸을 추가하셨는지 확인해주세요.")
                else:
                    st.warning("닉네임, 마트 위치, 비밀번호, 정보를 모두 입력해 주세요.")
            
    with tab3:
        st.header("🎯 장보기 전 필수! '호구 방지' 목표가 판독기")
        st.markdown("마트 가기 전 미리 확인하세요! 내가 사려는 물건, 도대체 **얼마면 잘 샀다고 소문이 날지** 빅데이터로 기준을 잡아드립니다.")
        st.write("---")
        
        def parse_unit_info(price, cap_str):
            if pd.isna(cap_str) or cap_str == '단일규격/기타': return None, None
            match = re.search(r'([0-9.]+)\s*([a-zA-Z가-힣]+)', str(cap_str))
            if not match: return None, None
            num = float(match.group(1))
            unit = match.group(2).lower()
            if unit == 'kg': num *= 1000; unit = 'g'
            elif unit == 'l': num *= 1000; unit = 'ml'
            elif unit in ['개입', '매', '캔', '팩', '봉', '인', '롤']: unit = '개'
            
            if num == 0: return None, None
            return price / num, unit

        categories_list = sorted(food_only_df['카테고리'].unique())
        
        col_a, col_b = st.columns(2)
        with col_a:
            calc_cat = st.selectbox("🛒 1. 구매할 상품 종류", categories_list, index=None, placeholder="👇 카테고리를 먼저 선택하세요", key='calc_cat')
        
        with col_b:
            if calc_cat:
                calc_items = sorted(food_only_df.loc[food_only_df['카테고리'] == calc_cat, '상품명'].unique())
                calc_item = st.selectbox("🥩 2. 정확한 상품명 선택", calc_items, index=None, placeholder="👇 상품명을 선택하세요", key='calc_item')
            else:
                st.selectbox("🥩 2. 정확한 상품명 선택", [], index=None, placeholder="👈 카테고리를 선택하면 활성화됩니다", disabled=True, key='calc_item_disabled')
                calc_item = None
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔍 목표가(적정가) 확인하기", type="primary", use_container_width=True):
            if not calc_item:
                st.warning("👆 목표가를 분석할 상품을 먼저 선택해 주세요!")
            else:
                calc_df = food_only_df[food_only_df['상품명'] == calc_item]
                avg_p = calc_df['판매가격'].mean()
                min_p = calc_df['판매가격'].min()
                max_p = calc_df['판매가격'].max()
                
                st.markdown("### 📊 빅데이터 목표가 분석 결과")
                st.markdown(f"현재 **[{calc_item}]**의 전국 마트 가격 분포입니다.")
                
                col_min, col_avg, col_max = st.columns(3)
                with col_min:
                    st.metric("📉 전국 최저가", f"{int(min_p):,}원")
                with col_avg:
                    st.metric("➖ 전국 평균가", f"{int(avg_p):,}원")
                with col_max:
                    st.metric("📈 전국 최고가", f"{int(max_p):,}원")
                    
                st.markdown("<hr style='margin: 10px 0 20px 0;'>", unsafe_allow_html=True)
                
                if min_p == max_p:
                    st.success(f"💡 **이 상품은 전국 마트 가격이 {int(min_p):,}원으로 모두 동일합니다!** (정찰제 또는 행사 동일 적용)\n\n어디서 사든 손해 보지 않으니 편하게 구매하세요.")
                else:
                    good_price = int((min_p + avg_p) / 2)
                    bad_price = int((avg_p + max_p) / 2)
                    
                    col_x, col_y, col_z = st.columns(3)
                    with col_x:
                        st.markdown(f"""
                        <div style="padding: 15px; border-radius: 8px; background-color: #d4edda; border: 1px solid #c3e6cb; text-align: center;">
                            <h3 style="margin: 0; color: #155724; font-size: 18px;">🔥 무조건 담으세요!</h3>
                            <p style="margin: 10px 0 0 0; font-size: 22px; font-weight: bold; color: #111;">{good_price:,}원 이하</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_y:
                        st.markdown(f"""
                        <div style="padding: 15px; border-radius: 8px; background-color: #e2e3e5; border: 1px solid #d6d8db; text-align: center;">
                            <h3 style="margin: 0; color: #383d41; font-size: 18px;">👍 훌륭한 적정가</h3>
                            <p style="margin: 10px 0 0 0; font-size: 20px; font-weight: bold; color: #333;">{good_price:,}원 ~ {bad_price:,}원</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_z:
                        st.markdown(f"""
                        <div style="padding: 15px; border-radius: 8px; background-color: #f8d7da; border: 1px solid #f5c6cb; text-align: center;">
                            <h3 style="margin: 0; color: #721c24; font-size: 18px;">🚨 카트에서 빼세요!</h3>
                            <p style="margin: 10px 0 0 0; font-size: 22px; font-weight: bold; color: #111;">{bad_price:,}원 이상</p>
                        </div>
                        """, unsafe_allow_html=True)
        
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.info("💡 **쇼핑 팁:** 마트에 가셨을 때 해당 상품의 가격표가 **초록색 상자 가격**에 가깝다면 주저 없이 구매하셔도 좋습니다!")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("#### 💡 혹시 평균가가 너무 비싸게 느껴지신다면?")
                
                keyword_groups = [
                    ['계란', '달걀'], ['우유'], ['치즈'], ['요거트'], ['버터'],
                    ['돼지고기', '삼겹살', '목살', '앞다리', '뒷다리'], ['소고기', '한우'], ['닭'], ['고등어'], ['오징어'],
                    ['감자'], ['고구마'], ['양파'], ['마늘'], ['배추'], ['쌀'],
                    ['라면'], ['만두'], ['스파게티'], ['햇반']
                ]
                
                matched_group = None
                for group in keyword_groups:
                    if any(kw in calc_item for kw in group):
                        matched_group = group
                        break
                
                base_alt_df = food_only_df[food_only_df['카테고리'] == calc_cat]
                if matched_group:
                    pattern = '|'.join(matched_group)
                    base_alt_df = base_alt_df[base_alt_df['상품명'].str.contains(pattern, na=False)]
                    
                alt_candidates = base_alt_df.groupby(['상품명', '용량'])['판매가격'].mean().reset_index()
                alt_candidates = alt_candidates[alt_candidates['상품명'] != calc_item]
                
                calc_cap = calc_df['용량'].iloc[0] if not calc_df.empty else '단일규격/기타'
                calc_unit_price, calc_base_unit = parse_unit_info(avg_p, calc_cap)
                
                recom_item = None
                is_bulk_discount = False
                
                if calc_unit_price is not None and not alt_candidates.empty:
                    def apply_unit_price(row):
                        up, u = parse_unit_info(row['판매가격'], row['용량'])
                        return pd.Series([up, u])
                    
                    alt_candidates[['단가', '기준단위']] = alt_candidates.apply(apply_unit_price, axis=1)
                    valid_alts = alt_candidates[(alt_candidates['기준단위'] == calc_base_unit) & (alt_candidates['단가'] < calc_unit_price)]
                    
                    if not valid_alts.empty:
                        recom_item = valid_alts.sort_values('단가').head(3).sample(1).iloc[0]
                        if recom_item['판매가격'] > avg_p:
                            is_bulk_discount = True
                else:
                    valid_alts = alt_candidates[alt_candidates['판매가격'] < avg_p]
                    if not valid_alts.empty:
                        recom_item = valid_alts.sort_values('판매가격').head(3).sample(1).iloc[0]
    
                if recom_item is not None:
                    if is_bulk_discount:
                        st.markdown(f"""
                        <div style="padding: 15px; border-radius: 8px; background-color: #fff9e6; border-left: 5px solid #ffc107;">
                            결제 금액은 조금 더 크지만, <b>용량 대비 가성비({recom_item['기준단위']}당 단가)</b>가 압도적으로 좋은 대용량 상품을 추천해 드립니다!<br><br>
                            오늘은 <b>{calc_item}</b> 대신, 가성비가 훌륭한 <b>[{recom_item['상품명']}] (평균 {int(recom_item['판매가격']):,}원)</b>(으)로 쟁여두는 건 어떨까요?
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="padding: 15px; border-radius: 8px; background-color: #f8f9fa; border-left: 5px solid #6c757d;">
                            오늘은 비싼 <b>{calc_item}</b> 대신,<br> 
                            평균 <b>{int(recom_item['판매가격']):,}원</b>으로 더 저렴한 <b>[{recom_item['상품명']}]</b>(으)로 장바구니를 채워보는 건 어떨까요?
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("💡 **현재 고르신 상품이 동종 카테고리 내에서 가장 가성비가 훌륭한 식재료입니다!** 비싸게 느낄 필요 없이 안심하고 구매하세요.")

except Exception as e:
    st.error("데이터 파일을 찾을 수 없습니다.")
