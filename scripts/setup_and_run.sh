#!/bin/sh
set -e

OCR_DIR="/app/models/models/OCR/paddleocr_torch"
mkdir -p /app/models/rapid_table
if [ -f "$OCR_DIR/Multilingual_PP-OCRv3_det_infer.pth" ]; then
    rm -f "$OCR_DIR/ch_PP-OCRv3_det_infer.pth"
    ln -s "$OCR_DIR/Multilingual_PP-OCRv3_det_infer.pth" "$OCR_DIR/ch_PP-OCRv3_det_infer.pth"
elif [ ! -e "$OCR_DIR/ch_PP-OCRv3_det_infer.pth" ] && [ -f "$OCR_DIR/ch_PP-OCRv5_det_infer.pth" ]; then
    ln -s "$OCR_DIR/ch_PP-OCRv5_det_infer.pth" "$OCR_DIR/ch_PP-OCRv3_det_infer.pth"
fi

MODEL_CHECK_PATHS="
/app/models/models/MFD/YOLO/yolo_v8_ft.pt
/app/models/models/Layout/YOLO/doclayout_yolo_docstructbench_imgsz1280_2501.pt
/app/models/models/OCR/paddleocr_torch/ch_PP-OCRv3_det_infer.pth
"

missing_models=0
for model_path in $MODEL_CHECK_PATHS; do
    if [ ! -f "$model_path" ]; then
        missing_models=1
        echo "Missing required model: $model_path"
    fi
done

if [ "$missing_models" -ne 0 ]; then
    echo "--- ERROR: Models Missing ---"
    echo "One or more MinerU models were not found under /app/models/models."
    echo "Please download the models on your host machine first:"
    echo "   python scripts/download_models.py"
    echo "----------------------------"
    exit 1
else
    echo "Models verified. Starting pipeline..."
fi

exec "$@"
