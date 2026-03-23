# 初めに
Twigは力学モデルを使用しないグラフ描画アプリです。
## 力学モデルを使わない理由
- 配置が勝手に動く
- 階層構造が直観的にわからない
- 描画が重い
## ターゲット
順序木(Orderd Tree)や、論理的な構造を整理したい人

# 特徴
## GML形式のサポート
既存のグラフデータの取り込みのためにGML形式に対応しています。
## 自動階層解析
どのノードがrootの場合でも、瞬時に親子構造を構築します。
## 空間最適化レイアウト
親の幅を子ノードの数で等分し、重なりのない配置を実現します。また、階層が深くなるほどノードの高さ（作業エリア）を拡大する独自設計により、深い階層での複雑な記述をサポートします。

# クイックスタート
Pythonスクリプトから簡単にレイアウトを計算できます。
```python
from gml_io import load, dump
from geometry import compute_layout
from drawing import draw

# グラフデータの読み込み
graph = load("test.gml")
graph2 = load("test2.gml")
# レイアウト計算
compute_layout(graph)
# 変数化
bind = build_hyper_edges(graph, [1,2,3])
# 代入
substitute = substitute_variable(bind, graph2, {1:1, 2:2, 3:3})
# 描画
draw(substitute)
# GML出力
dump("dump.gml", graph)

```