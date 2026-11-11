demo 项目 · 最小可跑版
=====================

结构
  blocks/    块的真身（一个块一个文件，data-block 是它的名字）
  archived/  抽屉（暂时不用的）
  meta/      blocks.json 清单 + tombs.json 贴条
  index.html 看板（开发态，由脚本生成）
  dist/      合成品（交付态，由脚本生成）

跑一遍
  python tools/kb.py scan              # 扫块、更新清单、重建看板与合成品
  python tools/kb.py status            # 看三态
  python tools/kb.py touch k-04 --back 12   # 把某块的时间倒推 12 天（演示用）
  python tools/kb.py archive           # 超 7 天没动的收进抽屉
  python tools/kb.py restore k-04      # 从抽屉取回
  python tools/kb.py tomb k-05 --why "为什么不行"
  python tools/kb.py index             # 建事实索引：哪个数字出现在哪些块
  python tools/kb.py impact "5000万"   # 改这个数字要读哪几块（不用读全文）
  python tools/kb.py checkup           # 体检：长度是否悬殊、句子有没有重复

四条规矩
  1. index.html 与 dist/demo.html 都由脚本生成，不手写
  2. 归档规则硬编码在脚本里，不靠人记
  3. 贴条必须写 --why，理由比内容值钱
  4. 改前先 impact，改后重跑 index 核对——不靠通读全文保证一致
