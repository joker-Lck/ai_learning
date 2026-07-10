# AI瀛︿範鏅鸿兘浣撶郴缁?- 瀹屾暣鏂囨。

> **鍩轰簬澶氭櫤鑳戒綋鐨勪釜鎬у寲瀛︿範璧勬簮鐢熸垚绯荤粺**  
> 姣旇禌绮剧畝鐗?- 鑱氱劍鏍稿績璧涢锛岀獊鍑烘妧鏈垱鏂?

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg)](https://nextjs.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://www.sqlite.org/)

---

## 馃搵 鐩綍

- [绯荤粺姒傝堪](#绯荤粺姒傝堪)
- [鏍稿績鐗规€(#鏍稿績鐗规€?
- [蹇€熷紑濮媇(#蹇€熷紑濮?
- [鎶€鏈灦鏋刔(#鎶€鏈灦鏋?
- [鏁版嵁搴撹璁(#鏁版嵁搴撹璁?
- [鍔熻兘妯″潡](#鍔熻兘妯″潡)
- [API鎺ュ彛](#api鎺ュ彛)
- [鍒涙柊浜偣](#鍒涙柊浜偣)
- [鏍稿績绠楁硶锛氭贩鍚堟绱㈢郴缁燂紙KNN + ANN锛塢(#鏍稿績绠楁硶娣峰悎妫€绱㈢郴缁焝nn--ann)
  - [楂樼骇妫€绱㈡柟娉曪紙2023-2026 鏂板瀷绠楁硶锛塢(#7-楂樼骇妫€绱㈡柟娉?023-2026-鏂板瀷绠楁硶)
- [鎬ц兘鎸囨爣](#鎬ц兘鎸囨爣)
- [甯歌闂](#甯歌闂)
- **[妫€绱㈡妧鏈壒鐐规繁搴﹁В鏋怾(RETRIEVAL_TECHNICAL_FEATURES.md)** 猸?**NEW**

---

## 绯荤粺姒傝堪

鏈郴缁熼噰鐢?*澶氭櫤鑳戒綋鍗忓悓鏋舵瀯**鍜?*澶氭暟鎹簱璁捐**锛屼负楂樼瓑鏁欒偛瀛︾敓鎻愪緵**涓€у寲瀛︿範璧勬簮鐢熸垚**鏈嶅姟銆?

### 鏍稿績浼樺娍

- 馃幆 **瀵硅瘽寮忓鐢熺敾鍍?* - 鑷劧璇█鏋勫缓8缁村害鍔ㄦ€佺敾鍍?
- 馃 **澶氭櫤鑳戒綋鍗忓悓** - 6涓笓涓氭櫤鑳戒綋鍒嗗伐鍗忎綔
- 馃摎 **7绉嶈祫婧愮被鍨?* - 鏂囨。/鎬濈淮瀵煎浘/棰樺簱/瑙嗛/鍔ㄧ敾/浠ｇ爜/闃呰
- 馃梽锔?**澶氭暟鎹簱鏋舵瀯** - 8涓嫭绔嬫暟鎹簱锛屽姛鑳介殧绂?
- 馃洝锔?**闃插够瑙夋満鍒?* - RAG楠岃瘉+浜嬪疄鏍告煡+寮曠敤鏍囨敞
- 鈿?**娴佸紡杈撳嚭** - SSE瀹炴椂鎺ㄩ€佺敓鎴愯繘搴?
- 馃敀 **鍐呭瀹夊叏** - 鏁忔劅璇嶈繃婊?瀛︽湳瑙勮寖妫€鏌?

---

## 鏍稿績鐗规€?

### 1. 澶氭櫤鑳戒綋绯荤粺锛?涓笓涓氭櫤鑳戒綋锛?

| 鏅鸿兘浣?| 鑱岃矗 | 杈撳嚭 |
|--------|------|------|
| **Profile Agent** | 瀛︾敓鐢诲儚鏋勫缓 | 8缁村害鐢诲儚鏁版嵁 |
| **Resource Agent** | 瀛︿範璧勬簮鐢熸垚 | 7绉嶇被鍨嬭祫婧?|
| **Path Agent** | 瀛︿範璺緞瑙勫垝 | 涓€у寲瀛︿範璺緞 |
| **Tutor Agent** | 鏅鸿兘杈呭绛旂枒 | 澶氭ā鎬佸洖绛?|
| **Assessment Agent** | 瀛︿範鏁堟灉璇勪及 | 澶氱淮搴﹁瘎浼版姤鍛?|
| **Coordinator Agent** | 鍗忚皟鍣?| 浠诲姟鍒嗗彂涓庣粨鏋滃悎骞?|

### 2. 澶氭暟鎹簱鏋舵瀯锛?涓嫭绔嬫暟鎹簱锛?

| 鏁版嵁搴?| 鐢ㄩ€?| 琛ㄦ暟 |
|--------|------|------|
| **ai_auth** | 璁よ瘉涓庣敤鎴风鐞?| 2 |
| **ai_profiles** | 瀛︾敓鐢诲儚瀛樺偍 | 1 |
| **ai_resources** | 瀛︿範璧勬簮绠＄悊 | 2 |
| **ai_paths** | 瀛︿範璺緞瑙勫垝 | 2 |
| **ai_tutor** | 鏅鸿兘杈呭瀵硅瘽 | 3 |
| **ai_assessments** | 瀛︿範鏁堟灉璇勪及 | 2 |
| **ai_agents** | 鏅鸿兘浣撳崗浣滄棩蹇?| 2 |
| **ai_rag_knowledge** 猸?| RAG鐭ヨ瘑搴擄紙鏁欏璧勬枡锛?| 2 |

**鎬昏**: 8涓暟鎹簱锛?6寮犺〃

### 3. 7绉嶅涔犺祫婧愮被鍨?

1. 馃搫 **Document** - 鏂囨。璧勬枡
2. 馃 **Mindmap** - 鎬濈淮瀵煎浘
3. 鉂?**Quiz** - 娴嬮獙棰樼洰
4. 馃帴 **Video** - 瑙嗛璁茶В
5. 馃幀 **Animation** - 鍔ㄧ敾婕旂ず
6. 馃捇 **Code Case** - 浠ｇ爜妗堜緥
7. 馃摉 **Reading** - 闃呰鏉愭枡

### 4. 棣栭〉宸ヤ綔鍙?

绯荤粺棣栭〉涓?*鍔ㄦ€佸伐浣滃彴**锛屾墍鏈夋暟鎹粠鍚庣瀹炴椂鑾峰彇锛屼笌鐧诲綍鐢ㄦ埛缁戝畾锛?

| 鍖哄煙 | 鍔熻兘 | 鏁版嵁鏉ユ簮 |
|------|------|---------|
| **椤堕儴闂€?* | 鏄剧ず鐢ㄦ埛鍚?+ 绱瀛︿範澶╂暟/鏃堕暱 | `GET /dashboard/stats` |
| **缁熻鍗＄墖** | 瀛︿範璁板綍/鍏磋叮棰嗗煙/鐢熸垚璧勬簮/钖勫急寰呰ˉ | `GET /get-profile` |
| **缁х画瀛︿範** | 鏈€杩戠敓鎴愮殑璧勬簮鍒楄〃锛岀偣鍑荤洿鎺ラ瑙?| `GET /list-resources` |
| **鏈€杩戠敓鎴?* | 鎵€鏈?AI 鐢熸垚璧勬簮锛屾敮鎸佸脊绐楅瑙?| `GET /list-resources` |
| **浠婃棩寤鸿** | 鍩轰簬璁板繂绯荤粺鐨勪釜鎬у寲鎺ㄨ崘 | `GET /learning-recommendations` |
| **蹇€熷紑濮?* | AI闂瓟/璧勬簮鐢熸垚/瀛︿範璇勪及/涓婁紶鏂囨。 | 妯″潡鍏ュ彛 |
| **鍗忓悓鍔ㄦ€?* | 鏅鸿兘浣撴椿鍔ㄦ棩蹇楀疄鏃舵祦 | `GET /activity-logs` |

**椤甸潰鍒囨崲**锛氬伐浣滃彴涓庡姛鑳介€夋嫨椤甸€氳繃涓婁笅婊戝姩鍒囨崲锛坰croll-snap锛夛紝宸ヤ綔鍙板唴閮ㄥ唴瀹瑰彲鐙珛婊氬姩銆?

**Hero 蹇嵎鍏ュ彛**锛氱櫥鍏ュ悗 Hero 椤甸潰鎻愪緵涓や釜蹇嵎鎸夐挳锛?
- **瀛︿範鐪嬫澘** - 鐩存帴璺宠浆鍒板伐浣滃彴鍗＄墖鐣岄潰
- **鍔熻兘閫夋嫨** - 鐩存帴璺宠浆鍒版ā鍧楅€夋嫨椤甸潰

### 5. 8缁村害瀛︾敓鐢诲儚

- **knowledge_base** - 鐭ヨ瘑鍩虹
- **cognitive_style** - 璁ょ煡椋庢牸锛堣瑙?鍚/鍔ㄨ锛?
- **learning_goals** - 瀛︿範鐩爣
- **skill_level** - 鎶€鑳芥按骞筹紙鍒濈骇/涓骇/楂樼骇锛?
- **learning_preferences** - 瀛︿範鍋忓ソ鍒楄〃
- **strengths** - 浼樺娍鍒楄〃
- **weaknesses** - 鍔ｅ娍鍒楄〃
- **motivation** - 瀛︿範鍔ㄦ満

### 6. 鏃犻檺闀挎椂璁板繂鏋舵瀯锛堥泦鎴愬湪杈呭鏅鸿兘浣擄級

- **鐭湡璁板繂** - Token 绾т笂涓嬫枃绐楀彛锛岃嚜鍔ㄤ繚瀛樺璇濆巻鍙?
- **鎯呮櫙璁板繂** - 瀵硅瘽浜嬩欢鍜屽涔犲満鏅紝鎸夐噸瑕佹€ц“鍑?
- **璇箟璁板繂** - SPO 涓夊厓缁勪簨瀹炵煡璇嗭紝鏀寔鍐茬獊妫€娴嬩笌淇
- **瀹炰綋璁板繂** - KV 鐢诲儚瀛樺偍 + 鐭ヨ瘑鍥捐氨鍏崇郴
- **閬楀繕鏈哄埗** - 鍩轰簬鑹惧娴╂柉閬楀繕鏇茬嚎鐨勬櫤鑳借“鍑忥紙R = e^(-t/S)锛?
- **鍐茬獊淇** - 鑷姩妫€娴嬩簨瀹炵煕鐩撅紝涓夌瑙ｅ喅绛栫暐
- **璁板繂澧炲己闂瓟** - 鑷姩妫€绱㈢浉鍏宠蹇嗭紝鏋勫缓澧炲己涓婁笅鏂?
- **闆嗘垚鏋舵瀯** - 璁板繂鍔熻兘鐩存帴闆嗘垚鍦?TutorAgent 涓紝鏃犻渶鐙珛鏈嶅姟

### 7. 娣峰悎妫€绱㈢郴缁燂紙ANN + KNN + RRF锛?

- **KNN 鍏抽敭璇嶆绱?* - MySQL 鍏ㄦ枃绱㈠紩绮剧‘鍖归厤涓撲笟鏈
- **ANN 鍚戦噺妫€绱?* - 浣欏鸡鐩镐技搴﹁涔夊尮閰?
- **RRF 铻嶅悎鎺掑簭** - Reciprocal Rank Fusion 缁熶竴鎺掑簭
- **闃插够瑙夋満鍒?* - RAG 浼樺厛妫€绱?+ 浜嬪疄鏍告煡 + 寮曠敤鏍囨敞

---

## 蹇€熷紑濮?

### 鐜瑕佹眰

- Python 3.8+
- Node.js 18+
- MySQL 8.0+

### 蹇€熼厤缃紙鎺ㄨ崘锛?

```bash
# 涓€閿厤缃幆澧冿紙妫€鏌ヤ緷璧栥€佸垱寤簐env銆佸畨瑁呭寘銆佸垵濮嬪寲鏁版嵁搴擄級
setup.bat
```

### 鎵嬪姩閰嶇疆

#### 姝ラ1: 瀹夎渚濊禆

```bash
# 鍚庣渚濊禆
pip install -r backend/requirements.txt

# 鍓嶇渚濊禆
cd frontend && npm install && cd ..
```

### 姝ラ2: 閰嶇疆鐜鍙橀噺

```bash
# 澶嶅埗閰嶇疆鏂囦欢
cp .env.example .env

# 缂栬緫 .env锛屽～鍐欎互涓嬮厤缃細
# - SPARK_API_KEY锛堝繀闇€锛岃椋炴槦鐏?API Key锛?
# - 鎵€鏈夋暟鎹簱鐨勫瘑鐮侊紙AUTH_DB_PASSWORD绛?涓級
```

### 姝ラ3: 鍒濆鍖栨暟鎹簱

```bash
# 澶氭暟鎹簱鏋舵瀯 - 鍒涘缓8涓嫭绔嬫暟鎹簱
python scripts/init_databases_v7.2.py
```

**棰勬湡杈撳嚭**:
```
鉁?鏁版嵁搴?'ai_auth' 鍒涘缓鎴愬姛!
鉁?鏁版嵁搴?'ai_profiles' 鍒涘缓鎴愬姛!
... (鍏?涓暟鎹簱)
鉁?鎵€鏈夋暟鎹簱鍒濆鍖栧畬鎴?
```

### 姝ラ4: 鍒涘缓绠＄悊鍛樿处鎴?

```bash
python scripts/init_admin.py
```

榛樿璐﹀彿: `admin / admin123`

### 姝ラ5: 鍚姩鏈嶅姟

```bash
# 鏂瑰紡1: 浣跨敤鍚姩鑴氭湰 (Windows)
鍚姩v6.bat

# 鏂瑰紡2: 鎵嬪姩鍚姩
# 缁堢1 - 鍚庣
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 缁堢2 - 鍓嶇
cd frontend && npm run dev
```

### 姝ラ6: 璁块棶绯荤粺

- **鍓嶇鐣岄潰**: http://localhost:3000
- **API鏂囨。**: http://localhost:8000/docs
- **榛樿璐﹀彿**: admin / admin123

---

## 鎶€鏈灦鏋?

### 鏁翠綋鏋舵瀯鍥?

```
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?        鍓嶇 (Next.js 14)            鈹?
鈹? 鈥?鍗曢〉闈㈠簲鐢?(SPA)                  鈹?
鈹? 鈥?URL鍙傛暟鎺у埗妯″潡鍒囨崲               鈹?
鈹? 鈥?鏃犻〉闈㈣烦杞?                       鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
               鈹?HTTP + SSE
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈻尖攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?     API灞?(FastAPI)                 鈹?
鈹? 鈥?/api/agent/*   (鏍稿績)            鈹?
鈹? 鈥?/api/stream/*  (鏍稿績)            鈹?
鈹? 鈥?/api/auth/*    (璁よ瘉)            鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
               鈹?
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈻尖攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?   澶氭櫤鑳戒綋灞?(6涓笓涓氭櫤鑳戒綋)         鈹?
鈹? 鈥?Coordinator (鍗忚皟鍣?              鈹?
鈹? 鈥?Profile/Resource/Path            鈹?
鈹? 鈥?Tutor/Assessment                 鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
               鈹?
鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈻尖攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
鈹?     鏁版嵁灞?(MySQL 8.0)              鈹?
鈹? 鈥?8涓嫭绔嬫暟鎹簱鏋舵瀯                  鈹?
鈹? 鈥?RAG鐭ヨ瘑搴?(鏁欏涓庡涔犺祫鏂?         鈹?
鈹? 鈥?鍚戦噺宓屽叆鏀寔                      鈹?
鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
```

### 鎶€鏈爤

**鍓嶇**:
- Next.js 14 (React妗嗘灦)
- TypeScript (绫诲瀷瀹夊叏)
- Tailwind CSS (鏍峰紡)
- Framer Motion (鍔ㄧ敾)
- Zustand (鐘舵€佺鐞?

**鍚庣**:
- FastAPI (楂樻€ц兘API)
- Python 3.8+
- MySQL 8.0 (澶氭暟鎹簱)
- 璁鏄熺伀 API (澶фā鍨?
- SSE (娴佸紡杈撳嚭)

**AI鑳藉姏**:
- 澶氭櫤鑳戒綋鍗忓悓
- RAG妫€绱㈠寮?
- 鍚戦噺鐩镐技搴︽绱?
- 闃插够瑙夋満鍒?
- Spark-X2-Flash 鎺ㄧ悊妯″瀷
- 鍥剧墖鐢熸垚 (TTI API)
- OCR 鏂囧瓧璇嗗埆
- 璇煶鍚堟垚 (TTS API)

---

## 鏁版嵁搴撹璁?

### 澶氭暟鎹簱鏋舵瀯鐞嗗康

**涓轰粈涔堥渶瑕佸鏁版嵁搴擄紵**
- 鉁?**鍔熻兘闅旂**: 閬垮厤鏁版嵁鑰﹀悎
- 鉁?**鎬ц兘浼樺寲**: 閽堝鎬т紭鍖栦笉鍚屾暟鎹被鍨?
- 鉁?**鏄撲簬缁存姢**: 妯″潡鍖栬璁?
- 鉁?**楂樺彲鐢ㄦ€?*: 鏁呴殰闅旂
- 鉁?**鐏垫椿鎵╁睍**: 鏂板鍔熻兘涓嶅奖鍝嶇幇鏈夌郴缁?

### 鏁版嵁搴撳叧绯诲浘

```
ai_rag_knowledge (鏍稿績鐭ヨ瘑搴? 猸?
  鈫?琚?涓ā鍧椾緷璧?
  
ai_profiles (瀛︾敓鐢诲儚)
  鈫?琚?涓ā鍧椾緷璧?
  
ai_auth (璁よ瘉) 鈫?鍩虹鏈嶅姟
  
ai_resources, ai_paths, ai_tutor, ai_assessments
  鈫?鏍稿績鍔熻兘妯″潡
  
ai_agents (鍗忎綔鏃ュ織) 鈫?璁板綍灞?
```

### 鏍稿績琛ㄧ粨鏋?

#### 1. ai_profiles.student_profiles (瀛︾敓鐢诲儚)

```sql
CREATE TABLE student_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    profile_data JSON NOT NULL COMMENT '{
        "knowledge_base": "...",
        "cognitive_style": "...",
        "learning_goals": "...",
        "skill_level": "...",
        "learning_preferences": [...],
        "strengths": [...],
        "weaknesses": [...],
        "motivation": "..."
    }',
    conversation_log JSON,
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 2. ai_resources.learning_resources (瀛︿範璧勬簮)

```sql
CREATE TABLE learning_resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    resource_type ENUM('document', 'mindmap', 'quiz', 'video', 
                       'animation', 'code_case', 'reading') NOT NULL,
    subject VARCHAR(50),
    topic VARCHAR(100),
    difficulty_level ENUM('beginner', 'intermediate', 'advanced'),
    content_data JSON NOT NULL,
    generated_by_agent VARCHAR(50),
    target_profile JSON,
    usage_count INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. ai_rag_knowledge.knowledge_documents (RAG鐭ヨ瘑搴?

```sql
CREATE TABLE knowledge_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    subject VARCHAR(50),
    document_type VARCHAR(50),
    content TEXT,
    embedding_vector JSON COMMENT '鍚戦噺宓屽叆',
    file_path VARCHAR(500),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. ai_memory (璁板繂绯荤粺)

```sql
-- 鐭湡璁板繂锛歍oken 绾т笂涓嬫枃绐楀彛
CREATE TABLE short_term_memory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    token_count INT DEFAULT 0
);

-- 璇箟璁板繂锛歋PO 涓夊厓缁勪簨瀹炵煡璇?
CREATE TABLE semantic_memory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    fact_type ENUM('preference', 'knowledge', 'skill', 'habit', 'goal', 'constraint'),
    subject VARCHAR(255) NOT NULL,
    predicate VARCHAR(255) NOT NULL,
    object TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.8
);

-- 瀹炰綋璁板繂锛欿V 鐢诲儚 + 鐭ヨ瘑鍥捐氨
CREATE TABLE entity_memory (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    entity_type ENUM('person', 'concept', 'skill', 'course', 'tool', 'organization'),
    entity_name VARCHAR(255) NOT NULL,
    attributes JSON,
    description TEXT
);

-- 璁板繂鍏冩暟鎹細閬楀繕鏈哄埗鎺у埗
CREATE TABLE memory_metadata (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    memory_type ENUM('short_term', 'episodic', 'semantic', 'entity', 'relation'),
    memory_id BIGINT NOT NULL,
    importance FLOAT DEFAULT 0.5,
    decay_rate FLOAT DEFAULT 0.1,
    is_forgotten BOOLEAN DEFAULT FALSE
);
```

---

## 鍔熻兘妯″潡

### 鍗曢〉闈㈠鑸郴缁?

**璁捐鐞嗗康**: 涓夊睆婊戝姩鍒囨崲锛屾棤椤甸潰璺宠浆锛岄€氳繃 scroll-snap 瀹炵幇鍏ㄥ睆椤甸潰鍒囨崲銆?

#### 涓夊睆甯冨眬

```
Section 0: Hero 棣栭〉         鈫?鍝佺墝灞曠ず + 缁熻姒傝
Section 1: 宸ヤ綔鍙?           鈫?鐢ㄦ埛鏁版嵁浠〃鐩橈紙鍐呴儴鍙粴鍔級
Section 2: 鍔熻兘閫夋嫨/妯″潡鍐呭  鈫?6澶фā鍧楀叆鍙ｆ垨鍏蜂綋妯″潡鍐呭
```

#### 宸ヤ綔鍙伴〉闈?

宸ヤ綔鍙版槸鐧诲綍鍚庣殑榛樿棣栭〉锛屾墍鏈夋暟鎹姩鎬佽幏鍙栵細
- 椤堕儴锛氶棶鍊欒 + 鐢ㄦ埛鍚?+ 瀛︿範澶╂暟/鏃堕暱缁熻
- 缁熻鍗＄墖锛氬涔犺褰?鍏磋叮棰嗗煙/鐢熸垚璧勬簮/钖勫急寰呰ˉ
- 缁х画瀛︿範锛氭渶杩戣祫婧愬垪琛紝鐐瑰嚮寮圭獥棰勮
- 浠婃棩寤鸿锛氬熀浜庤蹇嗙郴缁熺殑涓€у寲鎺ㄨ崘
- 鍗忓悓鍔ㄦ€侊細鏅鸿兘浣撴椿鍔ㄦ棩蹇?

#### 妯″潡瀵艰埅

```
馃搫 瀛︾敓鐢诲儚   鈫?URL鍙傛暟 ?module=profile
馃 璧勬簮鐢熸垚   鈫?URL鍙傛暟 ?module=resources
馃椇锔?瀛︿範璺緞   鈫?URL鍙傛暟 ?module=path
馃挕 鏅鸿兘杈呭   鈫?URL鍙傛暟 ?module=tutor
馃搱 鏁堟灉璇勪及   鈫?URL鍙傛暟 ?module=assessment
馃摎 鐭ヨ瘑搴?    鈫?URL鍙傛暟 ?module=rag
```

---

### 1. 瀛︾敓鐢诲儚妯″潡

**鍔熻兘**: 瀵硅瘽寮忔瀯寤?缁村害瀛︾敓鐢诲儚

**浣跨敤娴佺▼**:
1. 鐐瑰嚮渚ц竟鏍?瀛︾敓鐢诲儚"
2. 鍦ㄥ璇濇涓緭鍏ヤ釜浜轰俊鎭?
3. AI鍒嗘瀽骞舵瀯寤虹敾鍍?
4. 鏌ョ湅8缁村害鐢诲儚缁撴灉

**绀轰緥瀵硅瘽**:
```
鐢ㄦ埛: 鎴戞槸璁＄畻鏈虹瀛︿笓涓氬ぇ涓夊鐢燂紝瀵规満鍣ㄥ涔犲緢鎰熷叴瓒?
AI: 宸茶瘑鍒偍鐨勪笓涓氳儗鏅拰瀛︿範鍏磋叮...

鐢ㄦ埛: 鎴戞洿鍠滄閫氳繃瀹炶返鏉ュ涔?
AI: 宸叉洿鏂版偍鐨勫涔犲亸濂戒负"瀹炶返鍨?...

鐢诲儚鏋勫缓瀹屾垚锛佸凡璇嗗埆8涓淮搴︾壒寰併€?
```

**鏁版嵁绠＄悊**锛堢敾鍍忔ā鍧楀唴 Tab 鍒囨崲锛夛細
- **璇剧▼琛?*锛氭墜鍔ㄥ綍鍏?缂栬緫/鍒犻櫎 + 鏂囦欢瀵煎叆锛圥DF/Word/Excel/PPT/鍥剧墖锛夛紝AI 鑷姩璇嗗埆
- **鎴愮哗绠＄悊**锛氬綍鍏?+ 鏂囦欢瀵煎叆锛屾寜瀛︽湡缁熻
- **閿欓鏈?*锛氭坊鍔?鏍囪鎺屾彙/鍒犻櫎 + 鏂囦欢瀵煎叆
- **瀛︿範璁″垝**锛欰I 鐢熸垚 + 鎵嬪姩鍒涘缓

鏂囦欢瀵煎叆鐗规€э細
- AI 浼樺厛鏍￠獙鍐呭绫诲瀷锛堣琛?鎴愮哗/閿欓锛夛紝涓嶅尮閰嶇洿鎺ユ姤閿?
- AI 璇嗗埆鏈熼棿鍒囨崲 Tab 涓嶄腑鏂瘑鍒繘绋?
- 璇嗗埆澶辫触鑷姩灞曞紑鎵嬪姩娣诲姞琛ㄥ崟
- 鏀寔鎵弿鐗?PDF 璇嗗埆锛堥€氳繃 PyMuPDF 杞浘鐗囧悗 OCR锛?
- 鍥剧墖鏂囦欢浼樺厛浣跨敤 OCR 鎻愬彇鏂囧瓧锛屽け璐ュ垯闄嶇骇鍒板妯℃€佽瑙夎瘑鍒?

---

### 2. 璧勬簮鐢熸垚妯″潡

**鍔熻兘**: 鏍规嵁瀛︾敓鐢诲儚鐢熸垚涓€у寲瀛︿範璧勬簮

**浣跨敤娴佺▼**:
1. 閫夋嫨瀛︾鍜屼富棰?
2. 閫夋嫨璧勬簮绫诲瀷锛堝彲澶氶€夛級
3. 璁剧疆闅惧害绾у埆
4. 鐐瑰嚮鐢熸垚锛岀瓑寰匒I鐢熸垚

**鏀寔鐨勮祫婧愮被鍨?*:
- 馃搫 鏂囨。璧勬枡
- 馃 鎬濈淮瀵煎浘
- 鉂?娴嬮獙棰樼洰
- 馃帴 瑙嗛璁茶В
- 馃幀 鍔ㄧ敾婕旂ず
- 馃捇 浠ｇ爜妗堜緥
- 馃摉 闃呰鏉愭枡

---

### 3. 瀛︿範璺緞妯″潡

**鍔熻兘**: 瑙勫垝涓€у寲瀛︿範璺緞

**浣跨敤娴佺▼**:
1. 杈撳叆瀛︿範鐩爣
2. AI鍒嗘瀽褰撳墠姘村钩
3. 鐢熸垚瀛︿範璺緞锛堝惈澶氫釜姝ラ锛?
4. 璺熻釜瀛︿範杩涘害

**璺緞缁撴瀯**:
```
瀛︿範鐩爣: 鎺屾彙娣卞害瀛︿範鍩虹
鎬绘楠? 5姝?
棰勮鏃堕暱: 10灏忔椂

姝ラ1: 绁炵粡缃戠粶鍩虹 (2灏忔椂)
  - 鎰熺煡鏈烘ā鍨?
  - 鍙嶅悜浼犳挱绠楁硶
  - 婵€娲诲嚱鏁?

姝ラ2: CNN鍗风Н绁炵粡缃戠粶 (2.5灏忔椂)
  - 鍗风Н鎿嶄綔
  - 姹犲寲灞?
  - 缁忓吀鏋舵瀯
...
```

---

### 4. 鏅鸿兘杈呭妯″潡

**鍔熻兘**: 鏅鸿兘闂瓟锛屽妯℃€佸搷搴旓紝璁板繂澧炲己

**浣跨敤娴佺▼**:
1. 杩涘叆杈呭妯″潡锛孉I 鑷姩鍙戦€佹杩庡紩瀵兼秷鎭?
2. 閫夋嫨瀛︾
3. 杈撳叆闂
4. AI 妫€绱?RAG 鐭ヨ瘑搴?+ 鐢ㄦ埛璁板繂涓婁笅鏂?
5. 鐢熸垚鍥炵瓟锛堝惈鍥捐В銆佺ず渚嬶級

**鍝嶅簲鐗圭偣**:
- 馃摑 鏂囧瓧瑙ｉ噴
- 馃搳 Mermaid鍥捐В
- 馃挕 浠ｇ爜绀轰緥
- 馃敆 鐭ヨ瘑寮曠敤婧簮

---

### 5. 鏁堟灉璇勪及妯″潡

**鍔熻兘**: 澶氱淮搴﹀涔犳晥鏋滆瘎浼?

**浣跨敤娴佺▼**:
1. 鐐瑰嚮"鐢熸垚璇勪及鎶ュ憡"
2. AI鍒嗘瀽瀛︿範鍘嗗彶
3. 鐢熸垚澶氱淮搴﹁瘎浼?
4. 鏌ョ湅鏀硅繘寤鸿

**璇勪及缁村害**:
- 鐭ヨ瘑鎺屾彙搴?
- 鎶€鑳藉簲鐢ㄨ兘鍔?
- 瀛︿範涓诲姩鎬?
- 闂瑙ｅ喅鑳藉姏
- 鍒涙柊鎬濈淮鑳藉姏

---

### 6. 鐭ヨ瘑搴撴ā鍧?

**鍔熻兘**: 鏂囨。涓婁紶 + KNN+ANN+RRF 娣峰悎妫€绱?

**浣跨敤娴佺▼**:
1. 鐐瑰嚮渚ц竟鏍?鐭ヨ瘑搴?
2. 鎷栨嫿鎴栭€夋嫨鏂囦欢涓婁紶锛堟敮鎸?TXT/MD/PDF/DOC/PPT锛屽崟鏂囦欢鏈€澶?20MB锛?
3. 鍙€夊～鍐欏绉戞爣绛?
4. AI 鑷姩瑙ｆ瀽鏂囨。銆佹彁鍙栫煡璇嗙偣銆佺敓鎴愭憳瑕?
5. 鏂囨。鍏ュ簱鍚庨€氳繃娣峰悎妫€绱㈠紩鎿庢绱?

**妫€绱㈣兘鍔?*:
- **KNN 鍏抽敭璇嶈矾寰?*锛歁ySQL FULLTEXT INDEX 绮剧‘鍖归厤涓撲笟鏈
- **ANN 鍚戦噺璺緞**锛欶AISS 璇箟鍖归厤鐩歌繎琛ㄨ揪
- **RRF 铻嶅悎鎺掑簭**锛氫袱鏉¤矾寰勭粨鏋滅粺涓€鎺掑簭
- **楂樼骇绛栫暐**锛欻yDE / Multi-Query / RAG-Fusion / Contextual / Graph-Enhanced

---

## API鎺ュ彛

### 瀛︿範鏅鸿兘浣揂PI锛堟牳蹇冿級

| 绔偣 | 鏂规硶 | 鍔熻兘 |
|-----|------|------|
| `/api/agent/build-profile` | POST | 鏋勫缓瀛︾敓鐢诲儚 |
| `/api/agent/generate-resources` | POST | 鐢熸垚瀛︿範璧勬簮 |
| `/api/agent/plan-path` | POST | 瑙勫垝瀛︿範璺緞 |
| `/api/agent/tutor` | POST | 鏅鸿兘杈呭绛旂枒 |
| `/api/agent/assess` | POST | 瀛︿範鏁堟灉璇勪及 |
| `/api/agent/list-resources` | GET | 鑾峰彇璧勬簮鍒楄〃锛堟寜鐢ㄦ埛杩囨护锛?|
| `/api/agent/save-resource` | POST | 淇濆瓨璧勬簮鍒版暟鎹簱 |
| `/api/agent/dashboard/stats` | GET | 宸ヤ綔鍙扮粺璁℃暟鎹?|
| `/api/agent/activity-logs` | GET/POST | 娲诲姩鏃ュ織鏌ヨ/璁板綍 |
| `/api/agent/learning-recommendations` | GET | 涓€у寲瀛︿範鎺ㄨ崘 |

### 娴佸紡杈撳嚭涓庡畨鍏ˋPI锛堟牳蹇冿級

| 绔偣 | 鏂规硶 | 鍔熻兘 |
|-----|------|------|
| `/api/stream/generate-resource/{type}` | GET | 娴佸紡鐢熸垚璧勬簮(SSE) |
| `/api/stream/progress/{task_id}` | GET | 鏌ヨ浠诲姟杩涘害 |
| `/api/stream/check-content-safety` | POST | 鍐呭瀹夊叏妫€鏌?|
| `/api/stream/verify-fact` | POST | 浜嬪疄楠岃瘉 |

### 璁よ瘉API

| 绔偣 | 鏂规硶 | 鍔熻兘 |
|-----|------|------|
| `/api/auth/login` | POST | 鐢ㄦ埛鐧诲綍 |
| `/api/auth/register` | POST | 鐢ㄦ埛娉ㄥ唽 |
| `/api/auth/logout` | POST | 閫€鍑虹櫥褰?|

**瀹屾暣API鏂囨。**: http://localhost:8000/docs

---

## 鍒涙柊浜偣

### 1. 鐪熸鐨勫鏅鸿兘浣撴灦鏋?

- 鉁?6涓笓涓氭櫤鑳戒綋鍒嗗伐鍗忎綔
- 鉁?鍗忚皟鏅鸿兘浣撶粺涓€璋冨害
- 鉁?闈炲崟涓€AI妯″瀷璋冪敤

### 2. 7绉嶈祫婧愮被鍨嬪叏瑕嗙洊

- 鉁?瓒呭嚭姣旇禌瑕佹眰鐨?绉?
- 鉁?婊¤冻鍏ㄦ柟浣嶅涔犻渶姹?
- 鉁?涓€у寲鐢熸垚

### 3. 闃插够瑙変笁閲嶄繚闅?

- 鉁?RAG浼樺厛绛栫暐
- 鉁?浜嬪疄鏍告煡鏈哄埗
- 鉁?寮曠敤鏍囨敞婧簮

### 4. 娴佸紡杈撳嚭浣撻獙浼樺寲

- 鉁?SSE瀹炴椂杩涘害鎺ㄩ€?
- 鉁?5闃舵鍙鍖?
- 鉁?閬垮厤鐧藉睆绛夊緟

### 5. 鍐呭瀹夊叏淇濋殰

- 鉁?鏁忔劅璇嶆娴嬫嫤鎴?
- 鉁?瀛︽湳瑙勮寖妫€鏌?
- 鉁?绗﹀悎鏁欒偛鍦烘櫙瑕佹眰

### 6. 澶氭暟鎹簱鏋舵瀯鍒涙柊

- 鉁?8涓嫭绔嬫暟鎹簱
- 鉁?鍔熻兘瀹屽叏闅旂
- 鉁?RAG鐭ヨ瘑搴撲笓涓氬寲
- 鉁?鎬ц兘鎻愬崌3鍊?

### 7. 鍗曢〉闈㈠鑸郴缁?

- 鉁?淇濈暀瀵艰埅鑿滃崟
- 鉁?鏃犻〉闈㈣烦杞?
- 鉁?URL鍙傛暟鎺у埗
- 鉁?鐘舵€佷繚鎸?

### 8. 2023-2026 鍓嶆部妫€绱㈢畻娉?

- 鉁?HyDE 鍋囪鎬ф枃妗ｅ祵鍏ワ紙Gao et al., 2023锛?
- 鉁?Multi-Query 澶氭煡璇㈡绱紙LangChain, 2023锛?
- 鉁?RAG-Fusion + RRF 鏌ヨ铻嶅悎锛圧audaschl, 2023锛?
- 鉁?Contextual Retrieval 涓婁笅鏂囨绱紙Anthropic, 2024锛?
- 鉁?Graph-Enhanced RAG 鍥捐氨澧炲己妫€绱紙Microsoft, 2024锛?

### 9. 鍏ㄩ摼璺€ц兘浼樺寲

- 鉁?鍚庣锛歯umpy鍚戦噺鍖栬绠椼€丄C鑷姩鏈烘晱鎰熻瘝鍖归厤銆丩RU缂撳瓨
- 鉁?鍓嶇锛歊eact.memo銆佷唬鐮佸垎鍓层€丆SS contain銆亀ill-change
- 鉁?妫€绱細鍚戦噺璇箟妫€绱㈤檷绾х瓥鐣?

---

## 鏍稿績绠楁硶锛氭贩鍚堟绱㈢郴缁燂紙KNN + ANN锛?

> **馃摉 璇︾粏鎶€鏈枃妗?*锛氬叧浜庢绱㈡妧鏈殑娣卞害瑙ｆ瀽锛岃鍙傞槄 [妫€绱㈡妧鏈壒鐐规繁搴﹁В鏋怾(RETRIEVAL_TECHNICAL_FEATURES.md)锛屽叾涓寘鍚畬鏁寸殑鏋舵瀯鍥俱€佷唬鐮佸疄鐜般€佹€ц兘鎸囨爣鍜屽垱鏂版€荤粨銆?

鏈郴缁熷湪 RAG 鐭ヨ瘑搴撴绱腑璁捐浜嗕竴濂?*娣峰悎妫€绱㈠紩鎿?*锛岃瀺鍚堝悜閲忚涔夋绱紙ANN锛変笌鍏抽敭璇嶇簿纭尮閰嶏紙KNN锛夛紝閰嶅悎涓夌骇鍥為€€绛栫暐锛屽疄鐜颁簡楂樺彲鐢ㄣ€侀珮绮惧害鐨勭煡璇嗘绱㈣兘鍔涖€?

**娑夊強婧愭枃浠?*锛?

| 鏂囦欢 | 鏍稿績绫?鍑芥暟 | 琛屾暟 |
|------|-----------|------|
| `data/rag_knowledge_base.py` | `VectorIndexManager`锛堢52-205琛岋級銆乣RAGKnowledgeBase`锛堢210-918琛岋級 | 918琛?|
| `data/embedding_service.py` | `EmbeddingService`锛堢1-76琛岋級 | 76琛?|
| `data/qa_db_operations.py` | `QADatabase.search_similar_questions`锛堢153-209琛岋級 | 306琛?|
| `services/content_safety_service.py` | `AntiHallucinationService`锛堢195-344琛岋級 | 344琛?|

### 绠楁硶鏋舵瀯鎬昏

```
鐢ㄦ埛鏌ヨ
   鈹?
   鈹溾攢 KNN 鍏抽敭璇嶈矾寰?鈹€鈹€鈫?MySQL FULLTEXT INDEX 鈹€鈹€鈫?MATCH...AGAINST 鈹€鈹€鈫?Top-K 缁撴灉
   鈹?                       (涓撲笟鏈绮剧‘鍖归厤)
   鈹?
   鈹溾攢 ANN 鍚戦噺璺緞 鈹€鈹€鈫?Embedding(768缁? 鈹€鈹€鈫?FAISS ANN 妫€绱?鈹€鈹€鈫?Top-K 缁撴灉
   鈹?                                          鈹?
   鈹?                                   涓夌骇鍥為€€绛栫暐
   鈹?                                   鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹粹攢鈹€鈹€鈹€鈹€鈹€鈹?
   鈹?                                   鈹?            鈹?
   鈹?                             绱㈠紩宸插氨缁?   绱㈠紩鏈瀯寤?
   鈹?                                   鈹?       鑷姩鏋勫缓
   鈹?                                   鈹?            鈹?
   鈹?                                   鈻?            鈻?
   鈹?                             FAISS 鎼滅储    鎯版€ф瀯寤哄悗鎼滅储
   鈹?                                   鈹?
   鈹?                                   鈹? FAISS 涓嶅彲鐢?
   鈹?                                   鈻?
   鈹?                             鏆村姏浣欏鸡鍥為€€
   鈹?                             (numpy 鍚戦噺鍖?
   鈹?
   鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                   鈹?
                   鈻?
        鈹屸攢鈹€鈹€鈹€ RRF 铻嶅悎鎺掑簭 鈹€鈹€鈹€鈹€鈹?
        鈹? RRF(d)=危1/(k+rank)  鈹?
        鈹? 鍘婚噸 + Top-K 鎴柇   鈹?
        鈹斺攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
                   鈹?
                   鈻?
             娣峰悎妫€绱㈢粨鏋滐紙鍩哄骇锛?
                   鈹?
   鈹屸攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹尖攢鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹?
   鈹?              鈹?                      鈹?
   鈻?              鈻?                      鈻?
 HyDE          RAG-Fusion              Graph-Enhanced
 Multi-Query   Contextual              绛栫暐璺敱(smart_search)
```

---

### 1. 鏂囨湰鍚戦噺鍖栵紙Embedding Service锛?

**婧愭枃浠?*: `data/embedding_service.py` 鈫?`EmbeddingService` 绫伙紙绗?-76琛岋級

#### 鎶€鏈弬鏁?

| 鍙傛暟 | 鍊?| 璇存槑 |
|------|------|------|
| **API** | Kimi (Moonshot) Embedding API | `base_url: https://api.moonshot.cn/v1` |
| **妯″瀷** | `general` | 閫氱敤鏂囨湰宓屽叆妯″瀷 |
| **鍚戦噺缁村害** | `768` 缁?| 绌烘枃鏈繑鍥?`[0.0] * 768` 闆跺悜閲?|
| **鏂囨湰鎴柇** | `8000` 瀛楃 | 瓒呴暱鏂囨湰鑷姩鎴柇锛岄槻姝?API 瓒呮椂 |

#### 鏍稿績瀹炵幇

```python
# data/embedding_service.py 绗?3-54琛?
class EmbeddingService:
    def __init__(self):
        self._client = None
        self._api_key = None
        self._base_url = None

    @property
    def client(self):
        """鎳掑姞杞?OpenAI 鍏煎瀹㈡埛绔紝棣栨璋冪敤鏃舵墠鍒濆鍖?""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    def get_embedding(self, text, model='general'):
        """灏嗘枃鏈浆鎹负 768 缁寸瀵嗗悜閲?""
        text = text[:8000]                          # 鎴柇淇濇姢
        if not text.strip():
            return [0.0] * 768                      # 绌烘枃鏈繑鍥為浂鍚戦噺
        response = self.client.embeddings.create(model=model, input=text)
        return response.data[0].embedding           # 杩斿洖 768 缁?float 鍒楄〃

# 绗?7-76琛岋細浣欏鸡鐩镐技搴﹁绠楋紙KNN 鏆村姏鎼滅储鐨勫熀纭€锛?
    def cosine_similarity(self, vec1, vec2):
        """浣欏鸡鐩镐技搴?= dot(A,B) / (||A|| * ||B||)"""
        if vec1 is None or vec2 is None:
            return 0.0
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)

# 鍏ㄥ眬鍗曚緥锛堢75-76琛岋級
embedding_service = EmbeddingService()
```

---

### 2. ANN 杩戜技鏈€杩戦偦妫€绱紙FAISS 鍚戦噺绱㈠紩锛?

**婧愭枃浠?*: `data/rag_knowledge_base.py` 鈫?`VectorIndexManager` 绫伙紙绗?2-205琛岋級

#### 鎶€鏈柟妗?

| 椤圭洰 | 瀹炵幇 |
|------|------|
| **绱㈠紩绫诲瀷** | `faiss.IndexFlatIP`锛團lat Inner Product锛?|
| **鐩镐技搴﹀師鐞?* | L2 褰掍竴鍖栧悗鍐呯Н **绛変环浜?* 浣欏鸡鐩镐技搴︼細`normalize_L2(A) 路 normalize_L2(B) = cos(A,B)` |
| **鎼滅储澶嶆潅搴?* | O(n路d) 绮剧‘绾挎€ф壂鎻忥紙FlatIP 涓虹簿纭悳绱紝闈炶繎浼硷級 |
| **鎸佷箙鍖栬矾寰?* | `data/faiss_index/knowledge.index`锛團AISS 浜岃繘鍒讹級+ `data/faiss_index/doc_ids.json`锛圛D 鏄犲皠锛?|
| **骞跺彂瀹夊叏** | `threading.Lock` 淇濇姢鎵€鏈夌储寮曡鍐欐搷浣?|
| **鍚戦噺缁村害** | 768锛堜笌 Kimi Embedding 瀵归綈锛?|

#### 瀹屾暣鏍稿績浠ｇ爜锛堢63-205琛岋級

```python
# data/rag_knowledge_base.py 绗?2-205琛?
class VectorIndexManager:
    """
    鍩轰簬 FAISS 鐨勫悜閲忕储寮曠鐞嗗櫒
    - 鍐呭瓨椹荤暀绱㈠紩锛孫(n路d) 绮剧‘鏈€杩戦偦妫€绱?
    - 鑷姩鎸佷箙鍖栧埌纾佺洏锛岄噸鍚悗蹇€熷姞杞?
    - 鏂囨。鍙樻洿鏃舵儼鎬ч噸寤?
    """

    def __init__(self):                              # 绗?3-76琛?
        self._index = None                           # FAISS 绱㈠紩瀵硅薄
        self._doc_ids = []                           # 涓?FAISS 琛屽彿瀵归綈鐨勬枃妗?ID 鍒楄〃
        self._dimension = 0                          # 鍚戦噺缁村害
        self._lock = threading.Lock()                # 绾跨▼閿?
        self._dirty = False                          # 鏄惁鏈夋湭鎸佷箙鍖栫殑鍙樻洿
        self._faiss_available = False                # FAISS 鏄惁鍙敤
        try:
            import faiss as _faiss
            self._faiss = _faiss
            self._faiss_available = True
        except ImportError:
            self._faiss = None                       # FAISS 鏈畨瑁呮椂浼橀泤闄嶇骇

    def search(self, query_embedding: list, limit: int = 5) -> list:  # 绗?0-99琛?
        """妫€绱㈡渶鐩镐技鐨勬枃妗ｏ紝杩斿洖 [{'id': doc_id, 'score': float}, ...]"""
        with self._lock:
            if not self._faiss_available or self._index is None or self._index.ntotal == 0:
                return []
            vec = np.array([query_embedding], dtype='float32')
            self._faiss.normalize_L2(vec)            # L2 褰掍竴鍖栵細浣垮唴绉?= 浣欏鸡鐩镐技搴?
            k = min(limit, self._index.ntotal)
            scores, indices = self._index.search(vec, k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self._doc_ids):
                    continue
                results.append({
                    'id': self._doc_ids[idx],
                    'score': float(score)
                })
            return results

    def add_vectors(self, doc_ids: list, embeddings: list):  # 绗?01-118琛?
        """澧為噺娣诲姞鍚戦噺鍒扮储寮曪紙涓嶈Е鍙戝叏閲忛噸寤猴級"""
        if not doc_ids or not embeddings or not self._faiss_available:
            return
        with self._lock:
            dim = len(embeddings[0])
            if self._index is None:
                self._dimension = dim
                self._index = self._create_index(dim)
            elif dim != self._dimension:             # 缁村害鍙樺寲鏃跺己鍒堕噸寤?
                self._rebuild_internal([], [])
            vecs = np.array(embeddings, dtype='float32')
            self._faiss.normalize_L2(vecs)           # 褰掍竴鍖栧悗鍐嶅叆搴?
            self._index.add(vecs)                    # 澧為噺杩藉姞锛孫(1) 澶嶆潅搴?
            self._doc_ids.extend(doc_ids)
            self._dirty = True                       # 鏍囪闇€鎸佷箙鍖?

    def remove_by_ids(self, doc_ids: set):           # 绗?20-141琛?
        """鎸?ID 绉婚櫎鍚戦噺锛團AISS 涓嶆敮鎸佸師鐢熷垹闄わ紝閫氳繃 reconstruct + 閲嶅缓瀹炵幇锛?""
        with self._lock:
            if not self._faiss_available or self._index is None or not doc_ids:
                return
            keep_mask = [i for i, did in enumerate(self._doc_ids) if did not in doc_ids]
            if len(keep_mask) == len(self._doc_ids):
                return                               # 鏃犻渶鍒犻櫎
            if len(keep_mask) == 0:
                self._index = self._create_index(self._dimension)
                self._doc_ids = []
            else:
                # 鎻愬彇淇濈暀鍚戦噺 鈫?鍒涘缓鏂扮储寮?鈫?閲嶆柊娣诲姞
                all_vecs = np.array(
                    [self._index.reconstruct(i) for i in keep_mask], dtype='float32'
                )
                self._index = self._create_index(self._dimension)
                self._index.add(all_vecs)
                self._doc_ids = [self._doc_ids[i] for i in keep_mask]
            self._dirty = True

    def save(self):                                  # 绗?47-160琛?
        """鎸佷箙鍖栫储寮曞埌纾佺洏锛團AISS 浜岃繘鍒?+ JSON ID 鏄犲皠锛?""
        with self._lock:
            if not self._dirty or self._index is None:
                return
            os.makedirs(_INDEX_DIR, exist_ok=True)
            self._faiss.write_index(self._index, _INDEX_PATH)   # data/faiss_index/knowledge.index
            with open(_IDS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._doc_ids, f)                      # data/faiss_index/doc_ids.json
            self._dirty = False

    def load(self) -> bool:                          # 绗?62-176琛?
        """浠庣鐩樺姞杞界储寮曪紙閲嶅惎鍚庡揩閫熸仮澶嶏紝鏃犻渶閲嶆柊璁＄畻 embedding锛?""
        with self._lock:
            if not self._faiss_available:
                return False
            if not os.path.exists(_INDEX_PATH) or not os.path.exists(_IDS_PATH):
                return False
            self._index = self._faiss.read_index(_INDEX_PATH)
            with open(_IDS_PATH, 'r', encoding='utf-8') as f:
                self._doc_ids = json.load(f)
            self._dimension = self._index.d
            self._dirty = False
            return True

    @property
    def is_ready(self) -> bool:                      # 绗?78-179琛?
        return self._faiss_available and self._index is not None and self._index.ntotal > 0

    def _create_index(self, dim: int):               # 绗?01-205琛?
        """鍒涘缓 FAISS FlatIP 绱㈠紩锛堝綊涓€鍖栧悗鍐呯Н绛変环浣欏鸡鐩镐技搴︼級"""
        if dim <= 0 or not self._faiss_available:
            return None
        return self._faiss.IndexFlatIP(dim)

# 鍏ㄥ眬鍗曚緥锛堢207-208琛岋級
vector_index = VectorIndexManager()
```

#### 鍏抽敭甯搁噺

| 甯搁噺 | 鍊?| 浣嶇疆 |
|------|------|------|
| 绱㈠紩鐩綍 | `data/faiss_index/` | 绗?4琛?`_INDEX_DIR` |
| 绱㈠紩鏂囦欢 | `data/faiss_index/knowledge.index` | 绗?5琛?`_INDEX_PATH` |
| ID鏄犲皠鏂囦欢 | `data/faiss_index/doc_ids.json` | 绗?6琛?`_IDS_PATH` |

---

### 3. 涓夌骇鍥為€€妫€绱㈢瓥鐣?

**婧愭枃浠?*: `data/rag_knowledge_base.py` 鈫?`search_documents_by_vector`锛堢422-444琛岋級

绯荤粺瀹炵幇浜?*鑷姩闄嶇骇**鐨勬绱㈣矾鐢憋紝纭繚鍦ㄤ换浣曠幆澧冧笅閮借兘瀹屾垚鍚戦噺妫€绱細

```python
# data/rag_knowledge_base.py 绗?22-444琛?
def search_documents_by_vector(self, query_embedding, limit=5):
    """鍩轰簬鍚戦噺鐩镐技搴︽绱㈡枃妗ｏ紙浼樺厛 FAISS锛屽洖閫€鏆村姏鎼滅储锛?""

    # 鈹€鈹€ 璺緞 1: FAISS 绱㈠紩宸插氨缁?鈫?鐩存帴妫€绱紙鏈€蹇紝~5ms锛夆攢鈹€
    if vector_index.is_ready:
        return self._faiss_search(query_embedding, limit)

    # 鈹€鈹€ 璺緞 2: FAISS 鍙敤浣嗙储寮曟湭鏋勫缓 鈫?鎯版€ф瀯寤哄悗妫€绱紙棣栨 ~500ms锛夆攢鈹€
    if vector_index._faiss_available:
        try:
            self._build_faiss_index()               # 浠?MySQL 鍔犺浇鎵€鏈?embedding 鈫?鏋勫缓 FAISS 绱㈠紩
            if vector_index.is_ready:
                return self._faiss_search(query_embedding, limit)
        except Exception as e:
            warning(f"FAISS 绱㈠紩鏋勫缓澶辫触锛屽洖閫€鏆村姏鎼滅储: {e}")

    # 鈹€鈹€ 璺緞 3: FAISS 涓嶅彲鐢?鈫?鏆村姏 KNN 鍥為€€锛堜繚搴曪紝~100ms锛夆攢鈹€
    return self._brute_force_vector_search(query_embedding, limit)
```

| 鍥為€€绾у埆 | 瑙﹀彂鏉′欢 | 妫€绱㈡柟寮?| 鍝嶅簲鏃堕棿 |
|---------|---------|---------|---------|
| **L1** | `vector_index.is_ready == True` | FAISS `IndexFlatIP` 鍐呯Н鎼滅储 | ~5ms |
| **L2** | `_faiss_available == True` 浣嗙储寮曚负绌?| `_build_faiss_index()` 浠?DB 鍔犺浇 鈫?FAISS 鎼滅储 | ~500ms锛堥娆★級锛屽悗缁?~5ms |
| **L3** | `_faiss_available == False` 鎴栨瀯寤哄け璐?| `_brute_force_vector_search` 閬嶅巻璁＄畻浣欏鸡鐩镐技搴?| ~100ms |

#### 鎯版€х储寮曟瀯寤猴紙绗?81-498琛岋級

```python
# data/rag_knowledge_base.py 绗?81-498琛?
def _build_faiss_index(self):
    """浠庢暟鎹簱鍔犺浇鎵€鏈?embedding 鏋勫缓 FAISS 绱㈠紩锛堟儼鎬э紝棣栨鍚戦噺妫€绱㈡椂瑙﹀彂锛?""
    self.connect()
    sql = """SELECT id, document_data FROM knowledge_documents
             WHERE embedding IS NOT NULL"""
    self.cursor.execute(sql)
    rows = self.cursor.fetchall()

    doc_ids = []
    embeddings = []
    for row in rows:
        doc_data = row['document_data']
        if isinstance(doc_data, str):
            doc_data = json.loads(doc_data)
        emb = doc_data.get('embedding') if doc_data else None
        if emb and len(emb) > 0:
            doc_ids.append(row['id'])
            embeddings.append(emb)

    if embeddings:
        vector_index.rebuild(doc_ids, embeddings)    # 鍏ㄩ噺鏋勫缓绱㈠紩
        vector_index.save()                          # 鎸佷箙鍖栧埌纾佺洏
```

#### FAISS 妫€绱?+ 鎵归噺鍙栨枃妗ｏ紙绗?46-479琛岋級

```python
# data/rag_knowledge_base.py 绗?46-479琛?
def _faiss_search(self, query_embedding, limit):
    """FAISS 妫€绱?鈫?鎵归噺鏌ヨ鏂囨。璇︽儏 鈫?杩斿洖瀹屾暣缁撴灉"""
    hits = vector_index.search(query_embedding, limit)  # FAISS 鍚戦噺鎼滅储
    if not hits:
        return []

    doc_ids = [h['id'] for h in hits]
    score_map = {h['id']: h['score'] for h in hits}

    # 鎵归噺鏌ヨ鏂囨。璇︽儏锛堥伩鍏?N+1 闂锛?
    placeholders = ','.join(['%s'] * len(doc_ids))
    sql = f"""SELECT id, title, subject, document_type, content,
                     document_data, usage_count
              FROM knowledge_documents WHERE id IN ({placeholders})"""
    self.cursor.execute(sql, doc_ids)
    rows = self.cursor.fetchall()

    results = []
    for row in rows:
        doc = self._format_document(row)
        doc['vector_score'] = score_map.get(row['id'], 0)
        results.append(doc)

    # 鎸夊悜閲忕浉浼煎害寰楀垎闄嶅簭鎺掑垪
    results.sort(key=lambda x: x.get('vector_score', 0), reverse=True)
    return results
```

#### 鏆村姏 KNN 鍥為€€锛堢500-527琛岋級

```python
# data/rag_knowledge_base.py 绗?00-527琛?
def _brute_force_vector_search(self, query_embedding, limit=5):
    """FAISS 涓嶅彲鐢ㄦ椂鐨勫洖閫€鏂规锛氫粠 MySQL 鍔犺浇 embedding 鈫?閫愭潯璁＄畻浣欏鸡鐩镐技搴?""
    self.connect()
    sql = """SELECT id, title, subject, document_data
            FROM knowledge_documents
            WHERE document_data->>'$.embedding' IS NOT NULL
            LIMIT 100"""                             # 鏈€澶氬姞杞?100 鏉℃枃妗?
    self.cursor.execute(sql)
    rows = self.cursor.fetchall()

    results = []
    for row in rows:
        doc_data = row['document_data']
        if isinstance(doc_data, str):
            doc_data = json.loads(doc_data)
        doc_embedding = doc_data.get('embedding')
        if not doc_embedding:
            continue

        # 浣跨敤 EmbeddingService 鐨勪綑寮︾浉浼煎害璁＄畻
        similarity = embedding_service.cosine_similarity(query_embedding, doc_embedding)
        results.append({
            'id': row['id'],
            'title': row['title'],
            'subject': row['subject'],
            'vector_score': similarity
        })

    # 鎸夌浉浼煎害闄嶅簭鎺掑垪锛岃繑鍥?Top-K
    results.sort(key=lambda x: x['vector_score'], reverse=True)
    return results[:limit]
```

---

### 4. 鍏抽敭璇?Jaccard 鐩镐技搴﹀尮閰?

**婧愭枃浠?*: `data/rag_knowledge_base.py` 鈫?`search_documents`锛堢348-420琛岋級

闄や簡鍚戦噺璇箟妫€绱紝绯荤粺杩樺疄鐜颁簡鍩轰簬**璇嶉泦浜ら泦**鐨勫叧閿瘝绮剧‘鍖归厤锛岃鐩?鏁版嵁缁撴瀯 绗笁绔?杩欑被绮剧‘鏌ヨ鍦烘櫙銆?

#### 妫€绱㈡祦绋?

```python
# data/rag_knowledge_base.py 绗?48-420琛?
def search_documents(self, keywords, subject=None, limit=10):
    """鍏抽敭璇嶆悳绱細MySQL LIKE 绮楃瓫 鈫?Jaccard 鐩镐技搴︾簿鎺?鈫?TTL 缂撳瓨"""

    # 鈶?妫€鏌ョ紦瀛橈紙TTL 600绉掞紝LRU 涓婇檺 200 鏉★級
    cache_key = _get_cache_key("search_docs", (keywords[:50], subject, limit))
    cached = _get_cached_result(cache_key)
    if cached:
        return cached

    # 鈶?MySQL LIKE + JSON_SEARCH 绮楃瓫
    #    鍦?title銆乧ontent銆乻ubject銆乼ags 瀛楁涓悳绱㈠叧閿瘝
    sql = """SELECT id, title, subject, document_type, content,
                     document_data, usage_count
              FROM knowledge_documents
              WHERE (title LIKE %s OR content LIKE %s
                     OR subject LIKE %s OR JSON_SEARCH(tags, 'one', %s) IS NOT NULL)
              ORDER BY usage_count DESC
              LIMIT 50"""                            # 绮楃瓫鍙?50 鏉″€欓€?

    # 鈶?Jaccard 鐩镐技搴︾簿鎺?
    keyword_set = set(keywords.lower().split())
    for doc in candidates:
        text = f"{doc['title']} {doc.get('content', '')} {doc.get('subject', '')}"
        text_words = set(text.lower().split())
        common = len(keyword_set & text_words)       # 浜ら泦澶у皬
        total = len(keyword_set | text_words)        # 骞堕泦澶у皬
        similarity = common / total if total > 0 else 0  # Jaccard = |A鈭〣| / |A鈭狟|
        doc['keyword_score'] = similarity

    # 鈶?鎸夌浉浼煎害闄嶅簭鎺掑垪锛岃繑鍥?Top-K
    final_results.sort(key=lambda x: x.get('keyword_score', 0), reverse=True)
    final_results = final_results[:limit]

    # 鈶?缂撳瓨缁撴灉
    if final_results:
        _set_cache_result(cache_key, final_results)

    return final_results
```

#### Jaccard 鐩镐技搴﹀叕寮?

```
J(A, B) = |A 鈭?B| / |A 鈭?B|

绀轰緥锛?
  鏌ヨ: "鏈哄櫒瀛︿範 绁炵粡缃戠粶"  鈫?A = {"鏈哄櫒瀛︿範", "绁炵粡缃戠粶"}
  鏂囨。: "娣卞害瀛︿範涓庣缁忕綉缁滃熀纭€" 鈫?B = {"娣卞害瀛︿範涓庣缁忕綉缁滃熀纭€"}

  |A 鈭?B| = 1 ("绁炵粡缃戠粶")
  |A 鈭?B| = 3
  J = 1/3 鈮?0.33
```

---

### 5. 澶氬眰缂撳瓨鏈哄埗

绯荤粺鍦ㄤ袱涓暟鎹ā鍧椾腑瀹炵幇浜嗙嫭绔嬬殑 TTL 缂撳瓨锛岄噰鐢?*瀛楀吀 + 鏃堕棿鎴?*鐨?LRU 娣樻卑绛栫暐锛?

#### 缂撳瓨鍙傛暟瀵规瘮

| 鍙傛暟 | RAG 鐭ヨ瘑搴?(`rag_knowledge_base.py`) | QA 闂瓟搴?(`qa_db_operations.py`) |
|------|--------------------------------------|----------------------------------|
| **TTL** | `600` 绉掞紙绗?3琛岋級 | `300` 绉掞紙绗?1琛岋級 |
| **鏈€澶ф潯鐩?* | `200` 鏉★紙绗?1琛岋級 | `100` 鏉★紙绗?1琛岋級 |
| **娣樻卑绛栫暐** | 鍒犻櫎鏈€鏃ф潯鐩?| 鍒犻櫎鏈€鏃ф潯鐩?|
| **缂撳瓨閿墠缂€** | `rag:` | 鏃犲墠缂€ |
| **缂撳瓨绮掑害** | SQL + 鍙傛暟缁勫悎 | 闂鏂囨湰鍓?0瀛楃 |

#### 缂撳瓨瀹炵幇锛堜互 RAG 涓轰緥锛?

```python
# data/rag_knowledge_base.py 绗?2-40琛?
_query_cache = {}      # 鍏ㄥ眬缂撳瓨瀛楀吀 {key: (result, timestamp)}
_CACHE_TTL = 600       # 缂撳瓨杩囨湡鏃堕棿锛?00绉掞紙10鍒嗛挓锛?

def _get_cache_key(sql, params):
    """鐢熸垚缂撳瓨閿細rag:SQL璇彞:鍙傛暟"""
    return f"rag:{sql}:{str(params)}"

def _get_cached_result(cache_key):
    """鑾峰彇缂撳瓨缁撴灉锛岃繃鏈熻嚜鍔ㄥ垹闄?""
    if cache_key in _query_cache:
        result, timestamp = _query_cache[cache_key]
        if time.time() - timestamp < _CACHE_TTL:    # 鏈繃鏈?
            return result
        else:
            del _query_cache[cache_key]              # 杩囨湡鍒犻櫎
    return None

def _set_cache_result(cache_key, result):
    """鍐欏叆缂撳瓨锛岃秴杩囦笂闄愭椂娣樻卑鏈€鏃ф潯鐩?""
    _query_cache[cache_key] = (result, time.time())
    if len(_query_cache) > 200:                      # LRU 娣樻卑
        oldest_key = min(_query_cache.keys(), key=lambda k: _query_cache[k][1])
        del _query_cache[oldest_key]

def _clear_search_cache():
    """娓呴櫎鎵€鏈?RAG 鐩稿叧缂撳瓨锛堟枃妗ｅ彉鏇存椂璋冪敤锛?""
    keys_to_delete = [k for k in _query_cache.keys() if k.startswith('rag:')]
    for key in keys_to_delete:
        del _query_cache[key]
```

#### QA 闂瓟搴撶紦瀛橈紙绗?0-38琛岋級

```python
# data/qa_db_operations.py 绗?0-38琛?
_query_cache = {}
_CACHE_TTL = 300       # 缂撳瓨杩囨湡鏃堕棿锛?00绉掞紙5鍒嗛挓锛屾瘮 RAG 鐭紝鍥犱负闂瓟鍙樺寲鏇撮绻侊級

def _set_cache_result(cache_key, result):
    _query_cache[cache_key] = (result, time.time())
    if len(_query_cache) > 100:                      # 涓婇檺 100 鏉?
        oldest_key = min(_query_cache.keys(), key=lambda k: _query_cache[k][1])
        del _query_cache[oldest_key]
```

---

### 6. 鍙屾ā寮忔悳绱㈣瀺鍚堬紙KNN + ANN + RRF锛?

绯荤粺閲囩敤**涓夎矾娣峰悎妫€绱㈠紩鎿?*锛岃瀺鍚堝悜閲忚涔夋绱紙ANN锛変笌鍏抽敭璇嶇簿纭尮閰嶏紙KNN锛夛紝閰嶅悎 RRF 铻嶅悎鎺掑簭锛?

| 妫€绱㈣矾寰?| 绠楁硶 | 浼樺娍 | 閫傜敤鍦烘櫙 | 婧愭枃浠?|
|---------|------|------|---------|--------|
| **KNN 鍏抽敭璇嶈矾寰?* | MySQL `FULLTEXT INDEX` + `MATCH...AGAINST` | 绮剧‘鍖归厤涓撲笟鏈銆佸叕寮忋€佷唬鐮?| "姊害涓嬮檷" | `rag_knowledge_base.py` |
| **ANN 鍚戦噺璺緞** | FAISS `IndexFlatIP`锛堝綊涓€鍖栧唴绉?浣欏鸡鐩镐技搴︼級 | 鐞嗚В璇箟鐩歌繎琛ㄨ揪 | "浠€涔堟槸鏈哄櫒瀛︿範锛? | `rag_knowledge_base.py` |
| **RRF 铻嶅悎** | Reciprocal Rank Fusion | 鍏奸【绮剧‘涓庤涔?| 鎵€鏈夋煡璇?| `rag_knowledge_base.py` |

**铻嶅悎绛栫暐**: RRF锛圧eciprocal Rank Fusion锛夊€掓暟鎺掑簭铻嶅悎锛屽叕寮忎负锛?

```
RRF_score(d) = 危 1/(k + rank_i(d))

鍏朵腑 k=60锛堝父鏁帮級锛宺ank_i(d) 涓烘枃妗?d 鍦ㄧ i 鏉¤矾寰勪腑鐨勬帓鍚?
```

KNN 缁撴灉 + ANN 缁撴灉 鈫?RRF 缁熶竴鎺掑簭 鈫?Top-N 杩斿洖銆傚吋椤捐涔夌浉鍏虫€у拰鍏抽敭璇嶇簿纭害锛岄伩鍏嶅崟涓€璺緞鐨勭洸鍖恒€?

---

### 7. 楂樼骇妫€绱㈡柟娉曪紙2023-2026 鏂板瀷绠楁硶锛?

**婧愭枃浠?*: `services/advanced_retrieval_service.py` 鈫?`AdvancedRetrievalService` 绫?

绯荤粺鍦?KNN+ANN+RRF 娣峰悎鍩哄骇涔嬩笂锛屽疄鐜颁簡 5 绉?2023-2026 骞村墠娌挎绱㈡柟娉曪紝鎵€鏈夐珮绾х瓥鐣ュ潎浠ユ贩鍚堟绱负搴曞眰鍩哄骇锛?

| 鏂规硶 | 鏉ユ簮 | 鏍稿績鎬濇兂 | 閫傜敤鍦烘櫙 |
|------|------|----------|----------|
| **HyDE** | Gao et al., 2023 | LLM 鐢熸垚鍋囪绛旀锛岀敤绛旀鍚戦噺鍋?ANN 妫€绱?| 鐭煡璇€佹蹇垫€ч棶棰?|
| **Multi-Query** | LangChain, 2023 | LLM 鐢熸垚澶氫釜鏌ヨ鍙樹綋锛屾瘡涓彉浣撹蛋娣峰悎妫€绱?KNN+ANN)锛屽悎骞跺幓閲?| 鎻愰珮鍙洖鐜?|
| **RAG-Fusion + RRF** | Raudaschl, 2023 | 澶氭煡璇?+ 娣峰悎妫€绱?+ 鍊掓暟鎺掑悕铻嶅悎鎺掑簭 | 榛樿鎺ㄨ崘绛栫暐 |
| **Contextual Retrieval** | Anthropic, 2024 | 娣峰悎妫€绱㈢矖鍙洖 鈫?LLM 涓婁笅鏂囩浉鍏虫€х簿鎺?| 楂樼簿搴﹀満鏅?|
| **Graph-Enhanced RAG** | Microsoft GraphRAG, 2024 | 瀹炰綋鍥捐氨鎵╁睍鏌ヨ 鈫?娣峰悎妫€绱?| 鏈夊浘璋辨暟鎹椂 |

#### 绛栫暐璺敱锛?1 绉嶏級

```python
from services.advanced_retrieval_service import retrieval_service

# 鏅鸿兘璺敱锛氳嚜鍔ㄩ€夋嫨鏈€浣崇瓥鐣?
results = retrieval_service.smart_search(
    user_id=1, query="姊害涓嬮檷鍘熺悊", subject="鏈哄櫒瀛︿範",
    limit=5, strategy="auto"
)
```

| 绛栫暐 | 璇存槑 | 閫傜敤鍦烘櫙 |
|------|------|----------|
| `auto` | 鑷姩閫夋嫨锛堢煭鏌ヨ鐢?HyDE锛岄暱鏌ヨ鐢?RAG-Fusion锛?| 榛樿 |
| `knn` | KNN 鍏抽敭璇嶆绱紙MySQL FULLTEXT INDEX 绮剧‘鍖归厤锛?| 涓撲笟鏈銆佸叕寮?|
| `ann` | ANN 鍚戦噺妫€绱紙FAISS 璇箟鍖归厤锛?| 妯＄硦璇箟鏌ヨ |
| `hybrid` | KNN + ANN + RRF 娣峰悎锛堝熀搴х瓥鐣ワ級 | 閫氱敤鎺ㄨ崘 |
| `hyde` | 鍋囪鎬ф枃妗ｅ祵鍏ワ紙2023锛?| 鐭煡璇€佹蹇垫€ч棶棰?|
| `multi_query` | 澶氭煡璇㈡绱紙2023锛?| 鎻愰珮鍙洖鐜?|
| `rag_fusion` | RAG-Fusion + RRF锛?023锛?| 閫氱敤鎺ㄨ崘 |
| `contextual` | 涓婁笅鏂囩簿鎺掞紙2024锛?| 楂樼簿搴﹀満鏅?|
| `graph` | 鍥捐氨澧炲己妫€绱紙2024锛?| 鏈夊浘璋辨暟鎹椂 |
| `hybrid_advl` | 鍩哄骇 + HyDE + RAG-Fusion 涓夎矾 RRF | 骞宠　閫熷害涓庣簿搴?|
| `ensemble` | 鍏ㄩ儴 6 绉嶆柟娉曞彇骞堕泦锛孯RF 铻嶅悎 | 鏈€鍏ㄩ潰 |

#### 鏅鸿兘杈呭闆嗘垚

鏅鸿兘杈呭妯″潡鑷姩浣跨敤鍥捐氨澧炲己妫€绱紙Graph-Enhanced RAG锛夛紝浠庣敤鎴风煡璇嗗浘璋变腑鎻愬彇鍏宠仈瀹炰綋鎵╁睍鏌ヨ锛屽疄鐜颁釜鎬у寲鐭ヨ瘑鎺ㄨ崘銆?

---

### 8. 闃插够瑙?RAG 浜ゅ弶楠岃瘉

**婧愭枃浠?*: `services/content_safety_service.py` 鈫?`AntiHallucinationService` 绫伙紙绗?95-344琛岋級

AI 鐢熸垚鍐呭浼氱粡杩?RAG 鐭ヨ瘑搴撶殑浜ゅ弶楠岃瘉锛岃繖鏄?KNN 妫€绱㈢畻娉曞湪**鍐呭瀹夊叏**鍦烘櫙鐨勫簲鐢ㄣ€?

#### 鍏抽敭瀹炰綋鎻愬彇 + RAG 楠岃瘉锛堢204-253琛岋級

```python
# services/content_safety_service.py 绗?04-253琛?
def verify_with_rag(self, claim: str, knowledge_context: str,
                    threshold: float = 0.7) -> Dict:
    """
    鍩轰簬 RAG 鐭ヨ瘑搴撶殑浜嬪疄楠岃瘉
    1. 鎻愬彇澹版槑涓殑鍏抽敭瀹炰綋锛堝紩鍙峰唴瀹?+ 澶у啓涓撴湁鍚嶈瘝锛?
    2. 鍦ㄧ煡璇嗗簱涓婁笅鏂囦腑閫愪竴鏌ユ壘
    3. 璁＄畻缃俊搴?= 宸查獙璇佸疄浣撴暟 / 鎬诲疄浣撴暟
    4. 缃俊搴?< 0.7 鍒欐爣璁颁负"鍙兘瀛樺湪骞昏"
    """
    evidence = []
    contradictions = []
    key_entities = self._extract_key_entities(claim)  # 鎻愬彇寮曞彿鍐呭 + 涓撴湁鍚嶈瘝

    for entity in key_entities:
        if entity.lower() in knowledge_context.lower():   # 绠€鍗曞瓧绗︿覆鍖归厤
            evidence.append({"entity": entity, "found_in_context": True})
        else:
            contradictions.append({
                "entity": entity, "not_found": True,
                "warning": "璇ュ疄浣撴湭鍦ㄧ煡璇嗗簱涓壘鍒?鍙兘瀛樺湪骞昏"
            })

    total = len(key_entities)
    verified = len(evidence)
    confidence = verified / total if total > 0 else 0.5

    return {
        "is_verified": confidence >= threshold,      # 榛樿闃堝€?0.7
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "contradictions": contradictions,
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
```

#### 浜ゅ弶楠岃瘉 + 鏂囨湰鐩镐技搴︼紙绗?90-344琛岋級

```python
# services/content_safety_service.py 绗?90-317琛?
def cross_validate(self, primary_answer: str,
                   alternative_sources: List[str]) -> Dict:
    """
    灏嗕富鍥炵瓟涓庡涓浛浠ｆ潵婧愰€愪竴姣旇緝
    浣跨敤 Jaccard 鏂囨湰鐩镐技搴﹁绠椾竴鑷存€?
    涓€鑷存€?< 0.6 鍒欐爣璁颁负涓嶄竴鑷?
    """
    consistency_scores = []
    for source in alternative_sources:
        similarity = self._calculate_text_similarity(primary_answer, source)
        consistency_scores.append({
            "source_preview": source[:50] + "...",
            "similarity": round(similarity, 2)
        })

    avg_consistency = sum(s["similarity"] for s in consistency_scores) / len(consistency_scores)

    return {
        "average_consistency": round(avg_consistency, 2),
        "sources_checked": len(consistency_scores),
        "details": consistency_scores,
        "is_consistent": avg_consistency >= 0.6      # 涓€鑷存€ч槇鍊?
    }

# 绗?36-344琛岋細Jaccard 鏂囨湰鐩镐技搴?
def _calculate_text_similarity(self, text1: str, text2: str) -> float:
    """璁＄畻鏂囨湰鐩镐技搴︼紙绠€鍖栫増 Jaccard 鐩镐技搴︼級"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)            # J = |A鈭〣| / |A鈭狟|
```

#### 鍏抽敭甯搁噺

| 甯搁噺 | 鍊?| 浣嶇疆 |
|------|------|------|
| 鍙俊搴﹂槇鍊?| `0.7` | 绗?09琛?`threshold` 鍙傛暟榛樿鍊?|
| 涓€鑷存€ч槇鍊?| `0.6` | 绗?17琛?`avg_consistency >= 0.6` |

---

### 8. 闂瓟鍘嗗彶鐩镐技搴︽绱?

**婧愭枃浠?*: `data/qa_db_operations.py` 鈫?`search_similar_questions`锛堢153-209琛岋級

鍦ㄦ櫤鑳借緟瀵煎満鏅腑锛岀郴缁熶細鍏堢敤 KNN 妫€绱㈠巻鍙茬浉浼奸棶棰橈紝鍛戒腑鍒欑洿鎺ヨ繑鍥炲凡鏈夊洖绛旓紝閬垮厤閲嶅璋冪敤澶фā鍨嬨€?

#### 瀹屾暣瀹炵幇

```python
# data/qa_db_operations.py 绗?53-209琛?
def search_similar_questions(self, question_text, limit=5):
    """鎼滅储鐩镐技鍘嗗彶闂锛氬叧閿瘝鎻愬彇 鈫?MySQL LIKE 绮楃瓫 鈫?Jaccard 绮炬帓 鈫?TTL 缂撳瓨"""

    # 鈶?妫€鏌ョ紦瀛橈紙TTL 300绉掞紝涓婇檺 100 鏉★級
    cache_key = _get_cache_key("search_qa", question_text[:50])
    cached = _get_cached_result(cache_key)
    if cached:
        return cached

    # 鈶?鎻愬彇鍏抽敭璇嶏紙闀垮害 > 1 鐨勮瘝锛屾渶澶氬彇 3 涓級
    keywords = [kw for kw in question_text.split() if len(kw) > 1][:3]
    if not keywords:
        return []

    # 鈶?MySQL LIKE 绮楃瓫锛堝湪 question_text 鍜?ai_response 涓悳绱級
    like_conditions = []
    params = []
    for kw in keywords:
        like_conditions.append("question_text LIKE %s OR ai_response LIKE %s")
        params.extend([f"%{kw}%", f"%{kw}%"])

    sql = f"""SELECT id, question_text, ai_response, created_at
             FROM qa_records
             WHERE {" OR ".join(like_conditions)}
             ORDER BY created_at DESC
             LIMIT %s"""

    # 鈶?Jaccard 鐩镐技搴︾簿鎺?
    question_words = set(w.lower() for w in question_text.split() if len(w) > 1)
    enriched_results = []

    for result in results:
        # 灏嗗巻鍙查棶棰?+ 鍥炵瓟鍚堝苟涓鸿瘝闆嗗悎
        answer_words = set(w.lower() for w in
                          (result['question_text'] + ' ' + result['ai_response']).split()
                          if len(w) > 1)
        common_words = len(question_words & answer_words)   # 浜ら泦
        total_words = len(question_words | answer_words)    # 骞堕泦
        similarity = common_words / total_words if total_words > 0 else 0

        enriched_results.append({
            'id': result['id'],
            'question_text': result['question_text'],
            'ai_response': result['ai_response'],
            'similarity': similarity
        })

    # 鈶?鎸夌浉浼煎害闄嶅簭鎺掑垪
    enriched_results.sort(key=lambda x: x['similarity'], reverse=True)
    final_results = enriched_results[:limit]

    # 鈶?缂撳瓨缁撴灉
    if final_results:
        _set_cache_result(cache_key, final_results)

    return final_results
```

---

### 绠楁硶鍒涙柊鎬荤粨

| # | 鍒涙柊鐐?| 璇︾粏璇存槑 |
|---|--------|---------|
| 1 | **涓夌骇鍥為€€妫€绱㈢瓥鐣?* | FAISS 灏辩华 鈫?鑷姩鏋勫缓 FAISS 鈫?鏆村姏鎼滅储锛屼繚璇佺郴缁熷湪 FAISS 鏈畨瑁呮椂涔熻兘宸ヤ綔锛屽疄鐜颁簡浼橀泤闄嶇骇 |
| 2 | **FAISS 褰掍竴鍖栧唴绉?= 浣欏鸡鐩镐技搴?* | 閫氳繃 `normalize_L2` + `IndexFlatIP` 鐨勭粍鍚堬紝鐢ㄥ唴绉繍绠楅珮鏁堣绠椾綑寮︾浉浼煎害锛岄伩鍏嶄簡鏄惧紡璁＄畻浣欏鸡鍊肩殑寮€閿€ |
| 3 | **澧為噺绱㈠紩鏇存柊** | 鏂版枃妗ｅ叆搴撴椂澧為噺娣诲姞鍒?FAISS 绱㈠紩锛岄伩鍏嶅叏閲忛噸寤猴紱鍒犻櫎鏃舵墠瑙﹀彂閲嶅缓锛堝洜涓?FAISS 涓嶆敮鎸佸師鐢熷垹闄わ級 |
| 4 | **鎯版€х储寮曟瀯寤?* | 棣栨鍚戦噺妫€绱㈡椂鎵嶄粠鏁版嵁搴撳姞杞芥墍鏈?embedding 鏋勫缓 FAISS 绱㈠紩锛屽惎鍔ㄦ椂涓嶉樆濉?|
| 5 | **澶氬眰缂撳瓨鏈哄埗** | 鏌ヨ缁撴灉甯?TTL 缂撳瓨锛圧AG 缂撳瓨 600 绉掞紝QA 缂撳瓨 300 绉掞級锛孡RU 娣樻卑绛栫暐锛堜笂闄?200/100 鏉★級 |
| 6 | **涓夎矾娣峰悎妫€绱㈠紩鎿?* | KNN 鍏抽敭璇嶆绱紙MySQL FULLTEXT锛? ANN 鍚戦噺妫€绱紙FAISS锛? RRF 铻嶅悎鎺掑簭锛屽吋椤剧簿纭尮閰嶅拰璇箟鍖归厤 |
| 7 | **闃插够瑙?RAG 楠岃瘉** | 灏?AI 鐢熸垚鍐呭鐨勫叧閿疄浣撳湪 RAG 鐭ヨ瘑搴撲腑浜ゅ弶楠岃瘉锛岃绠楃疆淇″害锛屾爣娉ㄤ笉纭畾鎬ф潵婧?|
| 8 | **绾跨▼瀹夊叏璁捐** | `VectorIndexManager` 浣跨敤 `threading.Lock` 淇濇姢鎵€鏈夌储寮曡鍐欐搷浣滐紝閫傚悎 FastAPI 澶氱嚎绋嬬幆澧?|
| 9 | **numpy 鍚戦噺鍖栨毚鍔涙悳绱?* | 鏆村姏鍚戦噺鎼滅储浣跨敤 numpy 鐭╅樀鎵归噺璁＄畻浣欏鸡鐩镐技搴︼紝閫熷害鎻愬崌 10-100 鍊?|
| 10 | **AC 鑷姩鏈烘晱鎰熻瘝鍖归厤** | 鍐呭瀹夊叏鏈嶅姟浣跨敤 AC 鑷姩鏈虹畻娉曪紝瀹炵幇 O(n) 澶氭ā寮忓尮閰嶏紝鏇夸唬閫愯瘝閬嶅巻 |
| 11 | **LRU Cache 绾跨▼瀹夊叏缂撳瓨** | 浣跨敤 `collections.OrderedDict` 瀹炵幇 LRU 缂撳瓨锛屾敮鎸?TTL 杩囨湡鍜岀嚎绋嬪畨鍏?|
| 12 | **2023-2026 鍓嶆部妫€绱㈢畻娉?* | 闆嗘垚 HyDE銆丮ulti-Query銆丷AG-Fusion銆丆ontextual Retrieval銆丟raph-Enhanced RAG 浜旂鐜颁唬妫€绱㈡柟娉曪紝鍧囦互 KNN+ANN+RRF 娣峰悎妫€绱负鍩哄骇 |
| 13 | **11 绉嶇瓥鐣ヨ矾鐢?* | smart_search 缁熶竴鍏ュ彛鏀寔 11 绉嶆绱㈢瓥鐣ワ紝鎸夋煡璇㈢壒寰佽嚜鍔ㄨ矾鐢卞埌鏈€浣虫柟娉?|

---

## 鎬ц兘鎸囨爣

| 鎸囨爣 | 鏁板€?|
|-----|------|
| 鐢诲儚鏋勫缓 | <2绉?|
| 璧勬簮鐢熸垚 | 3-90绉?|
| SSE寤惰繜 | <200ms |
| 鍐呭瀹夊叏妫€鏌?| <100ms |
| API鍝嶅簲(P95) | <2绉?|
| 鏌ヨ鍝嶅簲鏃堕棿 | ~50ms |
| 骞跺彂杩炴帴鏁?| 800 |

---

## 浼佷笟绾х壒鎬?

### 瀹夊叏

| 鐗规€?| 璇存槑 |
|------|------|
| JWT 璁よ瘉 | HS256 绛惧悕锛宎ccess + refresh token 鍒嗙 |
| 閫熺巼闄愬埗 | 鍏ㄥ眬 120娆?鍒嗛挓锛岀櫥褰?10娆?鍒嗛挓锛屾敞鍐?5娆?鍒嗛挓 |
| 瀹夊叏澶?| X-Content-Type-Options, X-Frame-Options, HSTS, CSP |
| CORS | 鐜鍙橀噺閰嶇疆鐧藉悕鍗?|
| 杈撳叆鏍￠獙 | Pydantic 妯″瀷鑷姩鏍￠獙 |
| SQL 娉ㄥ叆闃叉姢 | 鍏ㄩ儴浣跨敤鍙傛暟鍖栨煡璇?|

### 鍙娴嬫€?

| 鐗规€?| 璇存槑 |
|------|------|
| 缁撴瀯鍖栨棩蹇?| JSON 鏍煎紡锛屾敮鎸佹棩蹇楄疆杞紙10MB/鏂囦欢锛屼繚鐣?0澶╋級 |
| 璇锋眰杩借釜 | 姣忎釜璇锋眰鍞竴 ID锛圶-Request-ID锛夛紝鍏ㄩ摼璺拷韪?|
| 鑰楁椂缁熻 | X-Response-Time 鍝嶅簲澶达紝涓棿浠惰嚜鍔ㄨ褰?|
| 鍋ュ悍妫€鏌?| `/api/health` 杩斿洖鍚勪緷璧栫姸鎬侊紙MySQL/FAISS锛?|

### 瀹瑰櫒鍖?

| 鐗规€?| 璇存槑 |
|------|------|
| Docker | 鍓嶅悗绔嫭绔嬮暅鍍忥紝闈?root 鐢ㄦ埛杩愯 |
| docker-compose | 涓€閿惎鍔紙鍚庣 + 鍓嶇 + MySQL + Redis锛?|
| 鍋ュ悍妫€鏌?| 瀹瑰櫒绾у埆鍋ュ悍妫€鏌ワ紝鑷姩閲嶅惎 |
| 璧勬簮闄愬埗 | 鍐呭瓨/CPU 闄愬埗閰嶇疆 |

### 鎬ц兘浼樺寲

| 鐗规€?| 璇存槑 |
|------|------|
| GZip 鍘嬬缉 | 鍝嶅簲浣?> 500 瀛楄妭鑷姩鍘嬬缉 |
| 杩炴帴姹?| MySQL 杩炴帴姹狅紙5杩炴帴锛夛紝澶嶇敤杩炴帴 |
| LRU 缂撳瓨 | 绾跨▼瀹夊叏鐨?TTL 缂撳瓨锛?00鏉?600绉掞級 |
| numpy 鍚戦噺鍖?| 鏆村姏鎼滅储 10-100 鍊嶅姞閫?|
| 鍓嶇浼樺寲 | React.memo銆佷唬鐮佸垎鍓层€丆SS contain |

### 浠ｇ爜璐ㄩ噺

| 鐗规€?| 璇存槑 |
|------|------|
| 绫诲瀷娉ㄨВ | 鍏紑 API 鍏ㄩ儴鏈夌被鍨嬫爣娉?|
| 閿欒杈圭晫 | 鍓嶇 ErrorBoundary 缁勪欢闅旂 |
| 闃叉姈/鑺傛祦 | useDebounce/useThrottledCallback hooks |
| 寮傚父澶勭悊 | 鍏ㄥ眬寮傚父澶勭悊鍣紝缁熶竴閿欒鏍煎紡 |

### 鍓嶇浼佷笟绾?

| 鐗规€?| 璇存槑 |
|------|------|
| 瀹夊叏澶?| X-Content-Type-Options / X-Frame-Options / HSTS / CSP |
| CSP | Content-Security-Policy 闄愬埗鑴氭湰/鏍峰紡/杩炴帴鏉ユ簮 |
| API閲嶈瘯 | 5xx/缃戠粶閿欒鑷姩閲嶈瘯2娆★紝鎸囨暟閫€閬?|
| 瓒呮椂鍒嗙骇 | 鏅€?0s / 鏂囦欢涓婁紶60s / AI鐢熸垚120s / 娴佸紡180s |
| XSS闃叉姢 | rehype-sanitize 杩囨护 Markdown 鎭舵剰HTML |
| 鍏冩暟鎹?| viewport / Open Graph / keywords / robots |
| 鐜鍒嗗眰 | .env.development / .env.production 鐙珛閰嶇疆 |
| Docker | standalone 杈撳嚭锛屽闃舵鏋勫缓 |

---

## 椤圭洰缁撴瀯

```
椤圭洰鏍圭洰褰?
鈹溾攢鈹€ backend/              # 鍚庣API
鈹?  鈹溾攢鈹€ api/
鈹?  鈹?  鈹溾攢鈹€ agent.py     # 澶氭櫤鑳戒綋API
鈹?  鈹?  鈹溾攢鈹€ stream.py    # 娴佸紡杈撳嚭
鈹?  鈹?  鈹斺攢鈹€ auth.py      # 璁よ瘉API
鈹?  鈹溾攢鈹€ main.py          # 搴旂敤鍏ュ彛锛堜紒涓氱骇閰嶇疆锛?
鈹?  鈹斺攢鈹€ dependencies.py  # JWT璁よ瘉銆佹潈闄愭牎楠?
鈹?
鈹溾攢鈹€ services/            # 涓氬姟閫昏緫
鈹?  鈹溾攢鈹€ agent_coordinator.py       # 鍗忚皟鏅鸿兘浣?
鈹?  鈹溾攢鈹€ profile_agent.py           # 鐢诲儚鏅鸿兘浣?
鈹?  鈹溾攢鈹€ resource_agent.py          # 璧勬簮鏅鸿兘浣?
鈹?  鈹溾攢鈹€ path_agent.py              # 璺緞鏅鸿兘浣?
鈹?  鈹溾攢鈹€ tutor_agent.py             # 杈呭鏅鸿兘浣擄紙闆嗘垚璁板繂澧炲己锛?
鈹?  鈹溾攢鈹€ assessment_agent.py        # 璇勪及鏅鸿兘浣?
鈹?  鈹溾攢鈹€ advanced_retrieval_service.py  # 楂樼骇妫€绱㈡湇鍔★紙5绉嶆柊鏂规硶锛?
鈹?  鈹溾攢鈹€ content_safety_service.py  # 鍐呭瀹夊叏锛圓C鑷姩鏈猴級
鈹?  鈹斺攢鈹€ streaming_service.py       # 娴佸紡杈撳嚭
鈹?
鈹溾攢鈹€ data/                # 鏁版嵁璁块棶
鈹?  鈹溾攢鈹€ rag_knowledge_base.py  # RAG鐭ヨ瘑搴擄紙FAISS+LRU缂撳瓨锛?
鈹?  鈹溾攢鈹€ db_operations.py       # 鏁版嵁搴撴搷浣?
鈹?  鈹溾攢鈹€ embedding_service.py   # 鍚戦噺鍖栨湇鍔?
鈹?  鈹斺攢鈹€ config.py              # 澶氭暟鎹簱閰嶇疆
鈹?
鈹溾攢鈹€ core/                # 鏍稿績宸ュ叿
鈹?  鈹溾攢鈹€ logger.py        # 缁撴瀯鍖栨棩蹇楋紙JSON+杞浆锛?
鈹?  鈹溾攢鈹€ json_utils.py    # 瀹归敊JSON瑙ｆ瀽
鈹?  鈹斺攢鈹€ prompts.py       # Prompt妯℃澘
鈹?
鈹溾攢鈹€ frontend/            # 鍓嶇搴旂敤
鈹?  鈹溾攢鈹€ components/
鈹?  鈹?  鈹溾攢鈹€ shared/
鈹?  鈹?  鈹?  鈹溾攢鈹€ ErrorBoundary.tsx    # 閿欒杈圭晫
鈹?  鈹?  鈹?  鈹斺攢鈹€ MarkdownRenderer.tsx # Markdown娓叉煋锛圶SS闃叉姢锛?
鈹?  鈹?  鈹斺攢鈹€ modules/                 # 6澶у姛鑳芥ā鍧?
鈹?  鈹溾攢鈹€ lib/
鈹?  鈹?  鈹溾攢鈹€ api.ts       # API瀹㈡埛绔紙閲嶈瘯+瓒呮椂锛?
鈹?  鈹?  鈹斺攢鈹€ hooks.ts     # 闃叉姈/鑺傛祦hooks
鈹?  鈹溾攢鈹€ middleware.ts     # 杈圭紭灞傚畨鍏ㄥご
鈹?  鈹溾攢鈹€ .env.development  # 寮€鍙戠幆澧冮厤缃?
鈹?  鈹斺攢鈹€ stores/index.ts   # Zustand鐘舵€佺鐞?
鈹?
鈹溾攢鈹€ scripts/             # 鍒濆鍖栬剼鏈?
鈹溾攢鈹€ resources/           # RAG鐭ヨ瘑搴撴枃浠?
鈹溾攢鈹€ Dockerfile           # 鍚庣瀹瑰櫒鍖?
鈹溾攢鈹€ docker-compose.yml   # 澶氭湇鍔＄紪鎺?
鈹溾攢鈹€ .env.example         # 鐜鍙橀噺妯℃澘
鈹斺攢鈹€ README.md
```

---

## 甯歌闂

### Q1: 濡備綍浣撶幇"澶氭櫤鑳戒綋"锛?

**A**: 绯荤粺鏈?涓笓涓氭櫤鑳戒綋锛堢敾鍍?璧勬簮/璺緞/杈呭/璇勪及/鍗忚皟锛夛紝鍒嗗伐鍗忎綔锛屼笉鏄崟涓€AI璋冪敤銆?

### Q2: 濡備綍淇濊瘉鍐呭鍑嗙‘鎬э紵

**A**: 涓夊眰闃叉姢: RAG浼樺厛妫€绱?鈫?浜嬪疄鏍告煡楠岃瘉 鈫?寮曠敤鏍囨敞婧簮銆?

### Q3: 娴佸紡杈撳嚭濡備綍瀹炵幇锛?

**A**: 浣跨敤SSE (Server-Sent Events)锛?涓樁娈靛疄鏃舵帹閫佽繘搴︼紝鍓嶇EventSource鎺ユ敹銆?

### Q4: 涓庝紶缁熻浠剁敓鎴愭湁浠€涔堝尯鍒紵

**A**: 浼犵粺璇句欢鏄浐瀹歅PT锛屾垜浠熀浜庣敾鍍忎釜鎬у寲鐢熸垚7绉嶈祫婧愮被鍨嬶紝鍔ㄦ€佽皟鏁撮毦搴︺€?

### Q5: 涓轰粈涔堥渶瑕佸鏁版嵁搴擄紵

**A**: 
- 鍔熻兘闅旂锛岄伩鍏嶆暟鎹€﹀悎
- 鎬ц兘浼樺寲锛岄拡瀵规€т紭鍖栦笉鍚屾暟鎹被鍨?
- 鏄撲簬缁存姢锛屾ā鍧楀寲璁捐
- 楂樺彲鐢紝鏁呴殰闅旂
- RAG鐭ヨ瘑搴撲笓涓氬寲

### Q6: 瀵艰埅涓轰粈涔堜笉璺宠浆椤甸潰锛?

**A**: 
- 鐢ㄦ埛浣撻獙鏇存祦鐣?
- 鐘舵€佷繚鎸佷笉鍙?
- 鍔犺浇閫熷害鏇村揩
- 閫氳繃URL鍙傛暟瀹炵幇妯″潡鍒囨崲

### Q7: 如何备份数据库？

**A**: 
```bash
# SQLite 数据库文件位于 data/databases/ 目录
# 直接复制 .db 文件即可备份
copy data\databases\*.db backup\
```bash
# 鍏ㄩ噺澶囦唤
  ai_auth ai_profiles ai_resources ai_paths \
  ai_tutor ai_assessments ai_agents ai_rag_knowledge \
  > backup_all.sql

# 鍗曠嫭澶囦唤RAG鐭ヨ瘑搴?
# SQLite 单独备份：copy data\databases\ai_rag_knowledge.db backup\
```

### Q8: 濡備綍瀵煎叆RAG鐭ヨ瘑搴撴暟鎹紵

**A**:
```bash
python scripts/init_rag_db.py
```

---

## 鎶€鏈敮鎸?

- **API鏂囨。**: http://localhost:8000/docs
- **闂鍙嶉**: 鏌ョ湅 `logs/` 鐩綍鏃ュ織
- **GitHub**: [椤圭洰鍦板潃]

---

