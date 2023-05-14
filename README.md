﻿# discord-bot
 
 ## 概要
 チャット上に入力されたコマンドを元にAPIを叩いて情報を出力するbot。
 `/help`コマンドでコマンドリストが表示される。
 
 ## コマンド簡易紹介
 - - -
 ### `/help`
 コマンドリストが出力される。
 - - -
 ### `/chatgpt` `/clearmemory`
 入力した文章をGPT-3.5のAPIとの会話、履歴の削除
 #### 引数
 - `input_text`
 APIへの入力文章
 - `system_text`
 入力した情報や設定などをAPIの呼び出し時の事前情報部分にセットする。
 - - -
 ### `/animeranking`
 Dアニメストアのランキングを取得し、 指定の順位まで表示する。
 - - -
 ### `$tenki`
 東京の天気予報をAPIから取得して表示する。
 - - -
 
