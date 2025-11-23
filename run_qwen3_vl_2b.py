from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
from PIL import Image
import torch

def main():
    # 1. 加载模型
    print("正在加载模型，这一步第一次会比较久，因为需要从 Hugging Face 下载权重...")
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen3-VL-2B-Instruct",
        torch_dtype="auto",      # 自动使用合适精度（通常 float16/bfloat16）
        device_map="auto",       # 自动把模型放到 GPU/CPU
    )

    # 2. 加载处理器
    processor = AutoProcessor.from_pretrained("Qwen/Qwen3-VL-2B-Instruct")

    # 3. 读取图片
    image = Image.open("test2.png").convert("RGB")

    # 4. 构造多模态对话
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": "请你告诉我这个截图是个什么网站，或者这个网页里最主要的信息是什么"},
            ],
        }
    ]

    # 5. 转成模型输入
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )

    # 6. 把输入移动到模型所在设备
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # 7. 生成
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=True,
            top_p=0.8,
            temperature=0.7,
        )

    # 8. 截掉前面的输入部分，只保留新生成的
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
    ]

    # 9. 解码输出
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]

    print("\n=== 模型回答 ===\n")
    print(output_text)

if __name__ == "__main__":
    main()
