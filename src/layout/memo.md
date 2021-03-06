# Layout

　複数のWindow/Padをつくるときの配置を簡略化する。

　始点座標、サイズを画面比率で調整する。

```python
pad, win = LeftRightLayout(Pad, Window, 50%, 50%)
```

　複数のWindow/Padは決して重ね合わさらない。ぴったり隣り合うか、余白がある。

　レイアウトタイプは以下のとおり。

* flow（比率を直接指定する）
	* 横方向（左から右へ）
	* 縦方向（上から下へ）
* block（ブロック数によって比率が確定する）
	* 縦横等幅

　リサイズするかどうかでLayoutクラスの寿命をどうするか判断する。

* リサイズしない：Window/Pad生成時、一度だけLayoutメソッドを実行すればよい
* リサイズする：Window/PadインスタンスにLayoutインスタンスを保持する。アクセス可能にし、`window.resize()`と連動させる

　cursesでは端末のリサイズに反応できない。なのでユーザのキーイベントなどを契機にしてWindow/Padのリサイズをする。このときLayoutはリサイズに応じて比率を保ったまま拡大・縮小するよう実装したい。

## メソッド

　必要な要素はつぎのとおり。

* レイアウトアルゴリズム（Flow(横に並べる、縦に並べる)、Tile(縦横等幅)）
* 範囲（width, height）
* 比率（width, height）
* 対象（Window, Pad）

```python
laoyout(alg=, w=, h=, wr=, hr=, targets=[pad1, win1])
```
```python
laoyout(alg=, w=curses.COLS, h=curses.LINES, wr=50%, hr=50%, targets=[pad1, win1])
```

### アルゴリズム別

#### Flow

```python
flow_laoyout_left(w=, h=, wr=, hr=, targets=[pad1, win1])
flow_laoyout_right(w=, h=, wr=, hr=, targets=[pad1, win1])
```
```python
flow_laoyout_left(w=curses.COLS, h=curses.LINES, wr=[50%,50%], hr=[50%,50%], targets=[pad1, win1])
flow_laoyout_right(w=curses.COLS, h=curses.LINES, wr=[50%,50%], hr=[50%,50%], targets=[pad1, win1])
```

　以下のように相対指定したいときもある。たとえばヘッダと本文のような単純構造のとき。1つ目のwindowは高さ=最小(1)、幅=最大(100%)で、2つ目のwindowは高さ=残り全部、幅=最大(100%)。

```python
flow_laoyout_left(w=curses.COLS, h=curses.LINES, wn=[最大(100%),50%], hn=[最小(1),50%], targets=[pad1, win1])
flow_laoyout_right(w=curses.COLS, h=curses.LINES, wn=[50%,50%], hn=[50%,50%], targets=[pad1, win1])
```

　このとき、`最小`,`最大`,`残り全部`,`自動`などの相対値を定数化しておく必要がある。`1`以上の整数値はサイズ指定に用いるため、負数をそれらにあてがう。

値|概要
--|----
`0`|自動（複数あれば`0`同士で等幅にする。`残り全部`があれば`自動`のところは`最小`にする）
`-1`|最小
`-2`|残り全部（`最小`や正数と組み合わせてひとつだけ許される。`自動`があれば`自動`のところは`最小`になる）
`-3`|最大（事実上使わない。なにせ最大化すれば１つしか表示できない。レイアウトの意義がない）

```
+-----------+-----------+
|Window1    |Window2    |
|50%        |50%        |
|           |           |
|           |           |
|           |           |
|           |           |
+-----------+-----------+
```

```
+-----------------------+
|Window1                |
|50%                    |
|                       |
|                       |
+-----------------------+
|Window2                |
|50%                    |
|                       |
|                       |
+-----------------------+
```

```
+-----------------------+
|Window1 header 1 line  |
+-----------------------+
|Window2 body 残り全部  |
|                       |
|                       |
|                       |
+-----------------------+
```

```
+-----------------------+
|Window1 header 1 line  |
+-----------------------+
|Window2 body 残り全部  |
|                       |
|                       |
|                       |
+-----------------------+
|Window3 footer 1 line  |
+-----------------------+
```

#### Block

```python
block_laoyout_left(w=, h=, wr=, hr=, targets=[pad1, win1])
block_laoyout_right(w=, h=, wr=, hr=, targets=[pad1, win1])
```
```python
block_laoyout_left(w=curses.COLS, h=curses.LINES, wr=[50%,50%], hr=[50%,50%], targets=[pad1, win1])
block_laoyout_right(w=curses.COLS, h=curses.LINES, wr=[50%,50%], hr=[50%,50%], targets=[pad1, win1])
```

```
+--------+ +--------+ +--------+
|        | |        | |        |
|        | |        | |        |
+--------+ +--------+ +--------+
+--------+ +--------+ +--------+
|        | |        | |        |
|        | |        | |        |
+--------+ +--------+ +--------+
+--------+ +--------+ +--------+
|        | |        | |        |
|        | |        | |        |
+--------+ +--------+ +--------+
```

# エラー

　Padの座標を変更できない。

```
    def X(self, v): self.__window.mvwin(self.Y, v)
_curses.error: mvwin() returned ERR
```
```
    def X(self, v): self.__window.mvderwin(self.Y, v)
_curses.error: mvderwin() returned ERR
```

　[mvwin][],[mvderwin][]の両方で試してみたが、どちらもダメだった。もしや、これらの関数はPadでは使えない？　Windowでしか使えない関数だったの？

　Padは[refresh][],[noutrefresh][]に6つの引数を渡す。それ以外はWindowと同じように使える。そう[Pythonのドキュメント](https://docs.python.org/ja/3/howto/curses.html#windows-and-pads)に書いてあったんですけど？

　APIドキュメントをよく見てみる。[newwin][]はX,Y座標を引数として受け取れる。でも、[newpad][]は受け取れない。もしや、この差異がなにか関係しているのか？　Padの実装がどうなっているか知らないけど、かならず`(0,0)`座標になる制約があるとか？　だからPadの座標を変更しようとするとエラーになったのでは？

[newpad]:https://docs.python.org/ja/3/library/curses.html#curses.newpad
[newwin]:https://docs.python.org/ja/3/library/curses.html#curses.newwin
[mvwin]:https://docs.python.org/ja/3/library/curses.html#curses.window.mvwin
[mvderwin]:https://docs.python.org/ja/3/library/curses.html#curses.window.mvderwin
[refresh]:https://docs.python.org/ja/3/library/curses.html#curses.window.refresh
[noutrefresh]:https://docs.python.org/ja/3/library/curses.html#curses.window.noutrefresh

## 結論

　Padは[mvwin][],[mvderwin][]できない。

　PadはWindowとまったく別物である。Windowとおなじように使えると思ったら痛い目をみる。[Pythonのドキュメント](https://docs.python.org/ja/3/howto/curses.html#windows-and-pads)では[refresh][],[noutrefresh][]に引数があること以外はおなじだと書いてあったが、嘘である。まったくのデタラメだった。だまされた。

### レイアウトするには？

　Padは[mvwin][],[mvderwin][]できない。Padは必ず`(0,0)`に配置される。それ以外の座標へは配置できない。

　ただ、[subpad][]は座標を受け付ける。もしや、[subpad][]なら座標を指定できるのでは？

[subpad]:https://docs.python.org/ja/3/library/curses.html#curses.window.subpad

　[subpad][]は[newpad][]の中に配置される。つまり最初に[newpad][]が必要だ。

　さらに[newpad][]自体は端末の物理サイズに合わせた表示にする。そして[subpad][]のほうをスクロール表示する。さらにもうひとつ別の[subpad][]をつくって、そちらは端末の物理サイズと固定位置で表示する。イメージは以下。

```
+--------------------------------+
|newpad                          |
|+--------------++--------------+|
||subpad1       ||subpad2       ||
||  scroll      ||  not scroll  ||
||              ||              ||
||              ||              ||
||              ||              ||
|+--------------++--------------+|
+--------------------------------+
```

　[subpad][]の座標をすこし右下へずらすと以下。

```
+----------------------------------+
|newpad                            |
|                                  |
|  +--------------++--------------+|
|  |subpad1       ||subpad2       ||
|  |  scroll      ||  not scroll  ||
|  |              ||              ||
|  |              ||              ||
|  |              ||              ||
|  +--------------++--------------+|
|                                  |
+----------------------------------+
```

　超めんどくさそう。たかがPadの座標が`(0,0)`固定なだけのせいで、大幅に実装をつくり変えねばならない予感。

　あと、PadとWindowを併用するときもある。Padの座標が`(0,0)`固定なのを妥協すれば、つぎのような構成にもできる。

```
+----------------------------------++----------------------+
|newpad                            |newwin                 |
|                                  |                       |
|  +--------------++--------------+|                       |
|  |subpad1       ||subpad2       ||                       |
|  |  scroll      ||  not scroll  ||                       |
|  |              ||              ||                       |
|  |              ||              ||                       |
|  |              ||              ||                       |
|  +--------------++--------------+|                       |
|                                  |                       |
+----------------------------------+-----------------------+
```

　でも、以下のように[newpad][]を`(0,0)`以外のところにはできない。WindowとPadはスクロールできるかどうかの違いだけであってほしい。Padになったとたんに座標を変更できなくなるとか、違和感しかない。まったくもって直感的じゃない。これはひどい。

```
+-----------------------++----------------------------------+
|newwin                 ||newpad                            |
|                       ||                                  |
|                       ||  +--------------++--------------+|
|                       ||  |subpad1       ||subpad2       ||
|                       ||  |  scroll      ||  not scroll  ||
|                       ||  |              ||              ||
|                       ||  |              ||              ||
|                       ||  |              ||              ||
|                       ||  +--------------++--------------+|
|                       ||                                  |
+-----------------------++----------------------------------+
```

　WindowとPadの違いを意識せずに座標を指定できるようにしたい。

　どうしたらいいのか。

* Window/Padの差分を吸収するコードを書く
* Windowクラスを継承して自前でPadクラスを書く
* そうまでしてTUIにこだわる価値はあるか？　もうやめようぜ？

　正直、もうやめたい。GUIのほうがいいんじゃない？

　既存ライブラリのクソっぷりを修正するとか苦痛すぎる。もしライブラリが変更されたら使えなくなるだろう。なので差分吸収パターンはなし。Window継承して自前Padをつくるのがマシ。ただ、それが苦痛すぎる。元々WindowとかPadのような便利クラスがあるからなんとかcursesでTUIを使おうという気になれた。なのに、それが使えないとなると、実装量がハンパない。すでに使いやすくするためのラッパクラスを書いている時点でクソすぎる。これ以上クソなら、もう使う価値なし。という結論になる。

　[Urwid][]というTUIライブラリがあるらしい。だが、TUIにこだわる理由がない。新しく学習せねばならなそう。なのに自由度も低い。だったらもうGUIを学習したほうがよいのでは？

[Urwid]:http://urwid.org/tutorial/

　[PySimpleGUI][]というGUIライブラリを学習したい。もうこれでいいじゃん。こっちのほうがいいじゃん。

[PySimpleGUI]:https://pysimplegui.readthedocs.io/en/latest/readme%20Japanese%20Version/

