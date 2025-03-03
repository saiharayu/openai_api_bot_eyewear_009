
import streamlit as st
import openai
import urllib.parse
import numpy as np
import pandas as pd

# OpenAI APIキーの取得（StreamlitのSecretsから）
try:
    if "openai_api_key" in st.secrets:
        openai.api_key = st.secrets["openai_api_key"]
    else:
        raise KeyError("OpenAI APIキーが見つかりません。StreamlitのSecretsに設定してください。")
except KeyError as e:
    st.error(f"❌ {e}")
    st.stop()

# 質問リスト（Q1で性別を確認）
questions = [
    {"text": "Q1. あなたの性別を選んでください", "choices": ["男性", "女性"]},
    {"text": "Q2. あなたの顔の印象に近いのは？", "choices": ["丸みがあり、やわらかい印象", "直線的で、シャープな印象", "スッキリと縦のラインが際立つ"]},
    {"text": "Q3. あなたの理想の雰囲気は？", "choices": ["知的で洗練された印象", "柔らかく親しみやすい雰囲気", "独自のスタイルを際立たせたい"]},
    {"text": "Q4. あなたのファッションスタイルは？", "choices": ["シンプルで洗練されたスタイル", "自然体でリラックスしたファッション", "個性的でトレンドを意識"]},
    {"text": "Q5. 眼鏡を主に使うシーンは？", "choices": ["仕事やフォーマルな場面で活躍させたい", "日常の相棒として、自然に取り入れたい", "ファッションのアクセントとして楽しみたい"]},
]

# `st.session_state` の初期化
for key in ["current_question", "answers", "submitted", "image_url", "result"]:
    if key not in st.session_state:
        st.session_state[key] = 0 if key == "current_question" else [] if key == "answers" else None

# 診断結果の生成（デザイン名を最初にし、250文字以内に要約）
def generate_result():
    gender = st.session_state["answers"][0]  # 性別取得
    answers_text = "\n".join([f"{q['text']} {a}" for q, a in zip(questions[1:], st.session_state["answers"][1:])])

    prompt = f"""
    You are a professional eyewear stylist. 
    Based on the user's responses, recommend a perfect glasses design with a short and stylish description.
    **Provide the response in Japanese within 250 characters.**

    User's gender: {gender}
    User's responses:
    {answers_text}

    Response format:
    -------------
    あなたにおすすめの眼鏡は【〇〇】です！
    （250文字以内で簡潔に、眼鏡の特徴や魅力を伝える）
    -------------
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"], gender

# 眼鏡デザインの画像を DALL·E で生成（不要な要素を排除）
def generate_glasses_image(description, gender):
    image_prompt = f"""
    A single stylish eyeglass: {description}. 
    Designed specifically for a {gender}.
    The eyeglasses should be the only object in the image, centered, with a plain, solid-colored background.
    No additional elements like text, labels, color variations, decorations, faces, or accessories.
    """

    response = openai.Image.create(
        model="dall-e-3",
        prompt=image_prompt,
        n=1,
        size="1024x1024"
    )

    return response["data"][0]["url"]

# タイトル表示
st.title("👓 眼鏡デザイン診断")
st.write("あなたにぴったりの眼鏡デザインを診断します！")

# 質問の表示
if st.session_state["current_question"] < len(questions):
    q = questions[st.session_state["current_question"]]
    st.subheader(q["text"])

    for choice in q["choices"]:
        if st.button(choice):
            st.session_state["answers"].append(choice)
            st.session_state["current_question"] += 1

            if st.session_state["current_question"] == len(questions):
                st.session_state["submitted"] = True

            st.experimental_rerun()

# 診断するボタンの表示
if st.session_state["submitted"] and not st.session_state["result"]:
    st.subheader("🎯 すべての質問に答えました！")
    if st.button("🔍 診断する"):
        result, gender = generate_result()
        st.session_state["result"] = result

        try:
            recommended_glasses = result.split("あなたにおすすめの眼鏡は【")[1].split("】です！")[0]
        except IndexError:
            recommended_glasses = "classic round metal frame glasses"

        st.session_state["image_url"] = generate_glasses_image(recommended_glasses, gender)

        st.experimental_rerun()

# 診断結果の表示
if st.session_state["result"]:
    st.subheader("🔮 診断結果")
    st.write(st.session_state["result"])

    if st.session_state["image_url"]:
        st.image(st.session_state["image_url"], caption="あなたにおすすめの眼鏡デザイン", use_column_width=True)

    # LINE共有ボタン
    share_text = urllib.parse.quote(f"👓 診断結果: {st.session_state['result']}")
    share_url = f"https://social-plugins.line.me/lineit/share?text={share_text}"
    st.markdown(f"[📲 LINEで友達に共有する]({share_url})", unsafe_allow_html=True)
