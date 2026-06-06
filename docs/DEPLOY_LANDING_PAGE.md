# GitHub Pages 閮ㄧ讲鎸囧崡 路 鐮佸尰 MediCode

> 5 鍒嗛挓鎶?`index.html` 閮ㄧ讲鍒?`username.github.io/medicode/`锛屾瘮璧涜瘎濮?鐣欏鎺ㄨ崘浜?鎶曡祫浜烘壂涓爜灏辫兘鐪嬨€?
---

## 涓€銆佹枃浠朵綅缃鏄?
鎴戜滑鍒氭墠鐢熸垚鐨?`index.html` 鏀惧湪**椤圭洰鏍圭洰褰?*锛?
```
鐮佸尰-MediCode/
鈹溾攢鈹€ index.html              鈫?椤圭洰瀹樼綉锛坙anding page锛?鈹溾攢鈹€ README.md
鈹溾攢鈹€ backend/
鈹溾攢鈹€ frontend/
鈹溾攢鈹€ docs/
鈹斺攢鈹€ ...
```

`index.html` 鏄?GitHub Pages 榛樿鏌ユ壘鐨勬枃浠跺悕锛屾斁鍦ㄦ牴鐩綍鏈€鐪佷簨銆?
---

## 浜屻€侀儴缃叉楠わ紙5 鍒嗛挓锛?
### 姝ラ 1锛氭妸 index.html 鎻愪氦鍒?GitHub

```powershell
# 鍦ㄩ」鐩牴鐩綍鎵ц
cd "C:\Users\Donghe\Desktop\鐮佸尰-MediCode"

# 鎻愪氦
git add index.html README.md
git commit -m "feat: 椤圭洰瀹樼綉 landing page + README SEO 鏀圭増"
git push origin master
```

> 鈿狅笍 **闇€瑕佸厛閰?GitHub 杩滅**銆傚鏋滆繕娌￠厤锛?> ```powershell
> # 1. 鍦?GitHub 缃戦〉涓婂垱寤虹┖浠撳簱 zshidonghe-code/MediCode-AI-medicode
> # 2. 鐒跺悗锛?> git remote add origin https://github.com/zshidonghe-code/MediCode-AI-medicode.git
> git push -u origin master
> ```

### 姝ラ 2锛氬紑鍚?GitHub Pages

1. 鎵撳紑 GitHub 浠撳簱椤甸潰 鈫?**Settings** 鈫?**Pages**
2. **Source**锛氶€?`Deploy from a branch`
3. **Branch**锛氶€?`master`锛堟垨 `main`锛岀湅浣犵敤浠€涔堬級 + `/ (root)`
4. 鐐瑰嚮 **Save**
5. 绛?30 绉?- 2 鍒嗛挓锛屽埛鏂伴〉闈細鏄剧ず锛?
> 鉁?Your site is live at `https://zshidonghe-code.github.io/MediCode-AI-medicode/`

### 姝ラ 3锛氳嚜瀹氫箟鍩熷悕锛堝彲閫夛級

濡傛灉浣犳湁鑷繁鐨勫煙鍚?`medicode.cn`锛?
1. 鍦?`docs/` 鍚岀骇鍒涘缓 `CNAME` 鏂囦欢锛?   ```
   medicode.cn
   ```
2. 鍦ㄥ煙鍚?DNS 娣诲姞 CNAME 璁板綍锛歚www` 鈫?`zshidonghe-code.github.io`
3. 鍦?GitHub Pages 璁剧疆濉叆 `medicode.cn`
4. 绛夊緟 DNS 鐢熸晥锛?0 鍒嗛挓 - 24 灏忔椂锛?
---

## 涓夈€侀儴缃插悗蹇呭仛楠岃瘉

### 3.1 鍩虹妫€鏌?
- [ ] 娴忚鍣ㄦ墦寮€ `https://zshidonghe-code.github.io/MediCode-AI-medicode/`
- [ ] 椤甸潰姝ｅ父鏄剧ず锛圚ero / 鍔熻兘 / 瀵规瘮琛?/ FAQ / CTA锛?- [ ] GitHub badges 姝ｅ父鏄剧ず
- [ ] 鎵€鏈夐摼鎺ュ彲鐐瑰嚮

### 3.2 SEO 楠岃瘉锛堝叧閿紒锛?
#### Google 鏀跺綍妫€鏌?
1. 鎵撳紑 [Google Search Console](https://search.google.com/search-console/)
2. 娣诲姞浣犵殑 GitHub Pages 鍩熷悕
3. 绛?1-3 澶?Google 鎶撳彇
4. 鎼滅储 `site:zshidonghe-code.github.io/MediCode-AI-medicode` 楠岃瘉鏀跺綍

#### Schema.org 楠岃瘉

1. 鎵撳紑 [Schema Markup Validator](https://validator.schema.org/)
2. 杈撳叆 URL锛歚https://zshidonghe-code.github.io/MediCode-AI-medicode/`
3. 搴旇鐪嬪埌 2 涓?schema锛?   - `SoftwareApplication` 鉁?   - `FAQPage` 鉁?
#### AI 寮曟搸寮曠敤娴嬭瘯

1. **ChatGPT**锛堝紑浜?web browsing锛夛細
   > 闂細"鏈夊摢浜?AI 鍖荤枟 DRG 缂栫爜鐨勫紑婧愰」鐩紵"
   > 鐪嬫槸鍚﹀紩鐢ㄤ綘鐨勯〉闈?
2. **Perplexity AI**锛?   > 鎼?"MediCode 鐮佸尰 AI 鍖荤枟缂栫爜"
   > 鐪嬫悳绱㈢粨鏋滄槸鍚﹀寘鍚?
3. **Google AI Overview**锛?   > 鎼?"AI 鍖荤枟 ICD 缂栫爜 鍑嗙‘鐜?
   > 鐪?AI 鎽樿鏄惁寮曠敤

> 馃挕 **AI 寮曠敤涓嶆槸绔嬪埢鐢熸晥**锛岄€氬父闇€瑕?2-4 鍛ㄦ寔缁敓浜у唴瀹癸紙鍗氬銆佹妧鏈枃绔狅級鎵嶈兘寤虹珛 domain authority銆?
### 3.3 绉诲姩绔祴璇?
- [ ] iPhone Safari 鎵撳紑姝ｅ父
- [ ] Android Chrome 鎵撳紑姝ｅ父
- [ ] 鎸夐挳鍙偣鍑伙紙涓嶉噸鍙狅級
- [ ] 瀛椾綋涓嶆孩鍑?
---

## 鍥涖€佸彲閫夊寮?
### 4.1 鍔?OG 鍥剧墖锛堢ぞ浜ゅ垎浜缉鐣ュ浘锛?
GitHub 浠撳簱鐨?`og-image.png` 寮曠敤浜?`zshidonghe-code.github.io/MediCode-AI-medicode/og-image.png`锛?*蹇呴』瀛樺湪**鎵嶈兘姝ｅ父鏄剧ず銆?
**鐢熸垚鏂规硶**锛?
1. 鎵撳紑 [https://www.bannerbear.com/](https://www.bannerbear.com/) 鎴?[https://www.canva.com/](https://www.canva.com/)
2. 鐢ㄦā鏉跨敓鎴?1200脳630 PNG
3. 鏀惧埌 `og-image.png`锛堥」鐩牴鐩綍锛?4. 閲嶆柊 push

**绠€鏄撴浛浠?*锛?
```powershell
# 鐢?PowerPoint 鍋氫竴涓?1200x630 灏侀潰锛屽鍑?PNG
# 鎴栫敤 ffmpeg 浠庝綘鐨?demo GIF 鎴竴甯?ffmpeg -i assets/demo-30s.gif -ss 00:00:10 -vframes 1 -y og-image.png
```

### 4.2 鍔?Google Analytics锛堟祦閲忓垎鏋愶級

鍦?`index.html` 鐨?`</head>` 鍓嶅姞锛?
```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

> 鎶?`G-XXXXXXXXXX` 鎹㈡垚浣犵殑 GA4 ID銆?
### 4.3 鍔?favicon

1. 鐢?[favicon.io](https://favicon.io/) 鐢熸垚 32脳32 ICO
2. 鏀惧埌 `favicon.ico`锛堥」鐩牴鐩綍锛?3. 鍦?`index.html` 鐨?`<head>` 鍔狅細
   ```html
   <link rel="icon" href="/favicon.ico" />
   ```

---

## 浜斻€丼EO 闀挎湡绛栫暐锛堜笉鍙?README锛?
| 棰戠巼 | 鍔ㄤ綔 | 宸ュ叿 |
|------|------|------|
| 姣忓懆 | 鍙?1 绡囨妧鏈崥瀹紙鐭ヤ箮/CSDN/鎺橀噾锛墊 Markdown + 澶栭摼鍥炰富椤?|
| 姣忔湀 | 鏇存柊 1 娆?BENCHMARK 鎶ュ憡 | 璺戞祴璇?鈫?鏇存柊鏁版嵁 |
| 姣忔湀 | 鐢宠 1 涓閾撅紙鍖荤枟琛屼笟缃戠珯/濯掍綋锛墊 濯掍綋鎶曠/閲囪 |
| 姣忓 | 鐢宠 1 娆″獟浣撴姤閬?| 36 姘?/ 铏庡梾 / 鍔ㄨ剦缃?|

> 鈴憋笍 **瑙佹晥鏃堕棿**锛?-6 涓湀鍚?ChatGPT/Perplexity 浼氫富鍔ㄥ紩鐢ㄤ綘銆?
---

## 鍏€佺揣鎬ユ儏鍐?
### 閮ㄧ讲鍚庨〉闈?404

1. 妫€鏌?GitHub Pages Settings 閲岀殑 Source 鏄惁姝ｇ‘
2. 妫€鏌ュ垎鏀悕锛坢aster vs main锛?3. 绛?5 鍒嗛挓锛孏itHub 缂撳瓨
4. 寮哄埗鍒锋柊娴忚鍣紙Ctrl+Shift+R锛?
### 閮ㄧ讲鍚庢牱寮忎贡鎺?
- 妫€鏌?`index.html` 鏄惁瀹屾暣涓婁紶
- 娴忚鍣?F12 鈫?Console 鐪嬫湁娌℃湁 404
- 妫€鏌?GitHub Pages URL 鏄惁甯?trailing slash

### 鎯虫崲鍥?docs/landing/

濡傛灉瑙夊緱 `index.html` 鍦ㄦ牴鐩綍纰嶄簨锛岀Щ璧帮細
```powershell
mkdir docs/landing
move index.html docs/landing/
# GitHub Pages Settings 鈫?Source 鏀规垚 /docs
```

---

## 涓冦€佷骇鍑烘竻鍗?
- [ ] `index.html`锛堝凡瀹屾垚锛屾牴鐩綍锛?- [ ] `README.md` 鏀圭増锛堝凡瀹屾垚锛孲EO 澧炲己锛?- [ ] `og-image.png`锛堝緟鐢熸垚锛?- [ ] `favicon.ico`锛堝彲閫夛級
- [ ] GitHub 杩滅閰嶇疆锛堝緟閰嶇疆锛?- [ ] GitHub Pages 寮€鍚紙寰呮搷浣滐級
- [ ] Google Search Console 楠岃瘉锛堝緟鎻愪氦锛?
> 瀹屾垚鍚庢妸杩欎釜 URL 鍙戝埌锛氱暀瀛︾敵璇锋潗鏂欍€佹瘮璧涙姤鍚嶈〃銆佹姇璧勪汉閭欢銆佺ぞ浜ゅ獟浣撲釜浜虹畝浠嬨€?
