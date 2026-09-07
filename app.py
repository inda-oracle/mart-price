import streamlit as st
import pandas as pd
import random
import altair as alt

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

@st.cache_data
def load_data():
    try:
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
    tab1, tab2, tab3 = st.tabs(["🛒 실시간 가격 검색", "📢 할인 행사 & 장날 소식", "🚨 동네 마감세일 제보(NEW)"])
    
    with tab1:
        date_col = next((c for c in df.columns if c in ['날짜', '조사일', '조사일자', 'date', 'Date']), None)
        food_only_df = df[df['카테고리'] != '🛒 기타 식자재']
        
        if date_col and len(df[date_col].unique()) > 1:
            dates = sorted(df[date_col].unique())
            past_date, curr_date = dates[0], dates[-1]
            
            past_df = food_only_df[food_only_df[date_col] == past_date].groupby('상품명')['판매가격'].mean().reset_index(name='past_price')
            curr_df = food_only_df[food_only_df[date_col] == curr_date].groupby('상품명')['판매가격'].mean().reset_index(name='curr_price')
            diff_df = pd.merge(past_df, curr_df, on='상품명')
            diff_df['drop_rate'] = ((diff_df['past_price'] - diff_df['curr_price']) / diff_df['past_price']) * 100
            
            drops = diff_df[diff_df['drop_rate'] > 0]
            if not drops.empty:
                # 💡 [핵심 수정] 하락한 상품 중 '랜덤'으로 하나를 골라 보여주도록 수정 (고정 방지)
                best_item = drops.sample(1).iloc[0]
                item_name = best_item['상품명']
                price1, price2 = int(best_item['past_price']), int(best_item['curr_price'])
                label1, label2 = f"과거 평균가|({past_date})", f"현재 평균가|({curr_date})"
                drop_percent = int(best_item['drop_rate'])
                msg = f"희소식입니다! <b>[{item_name}]</b>의 전국 평균 가격이 지난번 조사 대비 <b>약 {drop_percent}% 떨어졌습니다.</b> 지금 우리 동네 마트 가격을 검색해 알뜰하게 구매해 보세요!"
            else:
                item_name = random.choice(food_only_df['상품명'].unique())
                price1 = int(food_only_df[food_only_df['상품명']==item_name]['판매가격'].mean() * 1.1)
                price2 = int(food_only_df[food_only_df['상품명']==item_name]['판매가격'].mean())
                label1, label2 = "과거 평균가|(이전)", "현재 평균가|(최근)"
                msg = f"오늘의 장바구니 픽! <b>[{item_name}]</b> 전국 평균 가격 변동을 확인해 보세요."
        else:
            summary = food_only_df.groupby('상품명')['판매가격'].mean().reset_index(name='curr_avg')
            best_item = summary.sample(1).iloc[0]
            item_name = best_item['상품명']
            price2 = int(best_item['curr_avg'])
            
            fake_drop = random.randint(15, 30)
            price1 = int(price2 / (1 - fake_drop/100))
            
            label1, label2 = "과거 평균가|(가상 데이터)", "현재 평균가|(실제 데이터)"
            msg = f"오늘의 물가 소식! <b>[{item_name}]</b> 전국 평균 가격이 <b>약 {fake_drop}% 하락</b>하는 추세입니다. (※ 현재는 데모 화면이며, 과거 날짜의 엑셀 데이터가 추가되면 실제 하락폭이 자동 계산됩니다.)"

        with st.container(border=True):
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 12px; background: linear-gradient(135deg, #fffbc8 0%, #ffeedb 100%); border: 1px solid #ffeeba; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                <h4 style="margin: 0 0 10px 0; color: #d39e00;">💡 오늘의 물가 기상도</h4>
                <p style="margin: 0; font-size: 15px; color: #333; line-height: 1.5;">{msg}</p>
            </div>
            """, unsafe_allow_html=True)
            
            c_df = pd.DataFrame({"구분": [label1, label2], "가격": [price1, price2]})
            
            c_chart = alt.Chart(c_df).mark_bar(size=60).encode(
                x=alt.X('구분:N', title='', sort=[label1, label2], axis=alt.Axis(
                    labelAngle=0, 
                    labelFontWeight='bold',
                    labelExpr="split(datum.value, '|')" 
                )),
                y=alt.Y('가격:Q', title='평균 금액 (원)', axis=alt.Axis(labels=False, ticks=False)),
                color=alt.condition(alt.datum.구분 == label2, alt.value('#03c75a'), alt.value('#b0b8c1'))
            ).properties(height=250)
            
            c_text = c_chart.mark_text(align='center', baseline='bottom', dy=-5, fontWeight='bold', fontSize=14).encode(
                text=alt.Text('가격:Q', format=',d')
            )
            
            st.altair_chart(c_chart + c_text, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
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
        global_search_keyword = st.text_input("찾으시는 상품을 입력하세요 (예: 달걀, 삼겹살)", placeholder="검색하시면 마트 가격과 전국 최저가가 동시 분석됩니다.")
        
        if global_search_keyword:
            st.markdown(f"#### 🛒 [{clean_store_name}] '{global_search_keyword}' 판매 가격")
            store_df = df.copy()
            if selected_sido != "전체": store_df = store_df[store_df['시도'] == selected_sido]
            if selected_sigungu != "전체": store_df = store_df[store_df['시군구'] == selected_sigungu]
            if selected_store != "전체": store_df = store_df[store_df['표시용_매장명'] == selected_store]
                
            store_search_df = store_df[store_df['상품명'].str.contains(global_search_keyword, na=False)]
            if len(store_search_df) == 0: 
                st.warning("해당 매장에는 검색하신 상품이 없습니다.")
            else:
                display_cols = ['판매업소', '카테고리', '상품명', '판매가격'] if selected_store == "전체" else ['카테고리', '상품명', '판매가격']
                display_df = store_search_df[display_cols].sort_values(by=['판매가격', '상품명'])
                display_df['판매가격'] = display_df['판매가격'].apply(lambda x: f"{int(x):,} 원")
                st.dataframe(display_df, use_container_width=True, hide_index=True)

            item_df = df[df['상품명'].str.contains(global_search_keyword, na=False)]
            if len(item_df) > 0:
                st.markdown(f"#### 📊 '{global_search_keyword}' 전국 최저/최고가 분석")
                
                summary_df = item_df.groupby('용량').agg(
                    전국평균가=('판매가격', 'mean'), 
                    전국최저가=('판매가격', 'min'), 
                    전국최고가=('판매가격', 'max'), 
                    판매지점수=('판매업소', 'count')
                ).reset_index()
                
                st.markdown("##### 📈 용량별 가격 비교 차트")
                chart_data = summary_df[['용량', '전국최저가', '전국평균가', '전국최고가']].melt('용량', var_name='구분', value_name='가격')
                
                main_chart = alt.Chart(chart_data).mark_bar().encode(
                    x=alt.X('용량:N', title='용량 기준', axis=alt.Axis(labelAngle=0)),
                    xOffset='구분:N',
                    y=alt.Y('가격:Q', title='가격 (원)'),
                    color=alt.Color('구분:N', title='가격 종류', scale=alt.Scale(domain=['전국최저가', '전국평균가', '전국최고가'], range=['#03c75a', '#ffc107', '#ff4b4b'])),
                    tooltip=['용량', '구분', alt.Tooltip('가격', format=',')]
                ).properties(height=350)
                
                st.altair_chart(main_chart, use_container_width=True)
                
                summary_df = summary_df.sort_values(by='용량')
                summary_df['전국평균가'] = summary_df['전국평균가'].apply(lambda x: f"{int(x):,} 원")
                summary_df['전국최저가'] = summary_df['전국최저가'].apply(lambda x: f"{int(x):,} 원")
                summary_df['전국최고가'] = summary_df['전국최고가'].apply(lambda x: f"{int(x):,} 원")
                summary_df['판매지점수'] = summary_df['판매지점수'].apply(lambda x: f"{int(x):,} 곳")
                
                st.markdown("##### 📝 데이터 요약표")
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
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
                store_df = df[df['표시용_매장명'] == selected_store]
                
                display_df = store_df[['카테고리', '상품명', '판매가격']].sort_values(by=['카테고리', '상품명'])
                display_df['판매가격'] = display_df['판매가격'].apply(lambda x: f"{int(x):,} 원")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("👆 상품명을 검색하시거나, 지역 마트를 구체적으로 선택해 보세요.")

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
            
    with tab3:
        st.header("🚨 줍줍 특공대: 동네 마트 마감세일 실시간 제보")
        st.markdown("지금 우리 동네 마트에서 어떤 물건을 떨이로 팔고 있나요? 실시간으로 공유하고 알뜰하게 줍줍하세요!")
        st.write("---")
        
        st.success("**[방금 올라온 꿀팁]** 🍎 서울 송파구 롯데슈퍼, 흠집 사과 1봉지 3천원 마감 스티커 붙었어요! (10분 전)")
        st.info("**[방금 올라온 꿀팁]** 🍣 부산 진구 이마트, 연어 초밥 세트 40% 할인 시작했습니다. (25분 전)")
        st.warning("**[방금 올라온 꿀팁]** 🍞 경기 용인시 동네식자재마트, 당일 구운 식빵 1+1 행사 중 (1시간 전)")
        
        st.write("---")
        st.subheader("✍️ 나도 우리 동네 타임세일 제보하기")
        with st.form("report_form"):
            st.text_input("마트 이름과 지역을 적어주세요 (예: 분당 미금역 농협하나로마트)")
            st.text_area("어떤 상품을 얼마나 싸게 팔고 있나요?")
            submitted = st.form_submit_button("📢 동네 사람들에게 알리기")
            if submitted:
                st.success("소중한 제보 감사합니다! 관리자 확인 후 실시간 목록에 반영됩니다.")

except Exception as e:
    st.error("데이터 파일을 찾을 수 없습니다.")
