import sys

with open('d:/Project/FDA detectionV2/FDA-Detection/backend/app/api/endpoints.py', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''                        if ocr_engine.typhoon_key:
                            final_ocr_texts = ocr_engine.process_crops_parallel_dual(
                                cropped_images, context="fda", max_workers=4
                            )
                        else:
                            final_ocr_texts = ocr_engine.process_crops(cropped_images, context="fda")'''

replace1 = '''                        if ocr_engine.typhoon_key:
                            final_ocr_texts = await ocr_engine.process_crops_parallel_dual(
                                cropped_images, context="fda", max_workers=4
                            )
                        else:
                            final_ocr_texts = await ocr_engine.process_crops(cropped_images, context="fda")'''

target2 = '''                except Exception as ocr_err:
                    logger.error(f"  > OCR/Crop Error: {ocr_err}")
                
                cleaned_texts = [clean_text(t) for t in final_ocr_texts if t and t.strip()]'''

replace2 = '''                except Exception as ocr_err:
                    logger.error(f"  > OCR/Crop Error: {ocr_err}")
                    final_ocr_texts = []
                
                cleaned_texts = []
                for t in final_ocr_texts:
                    if isinstance(t, dict):
                        if t.get('text') and t.get('text').strip():
                            cleaned_texts.append(clean_text(t['text']))
                    else:
                        if t and str(t).strip():
                            cleaned_texts.append(clean_text(str(t)))'''

if target1 in content:
    content = content.replace(target1, replace1)
    print('Target 1 replaced')
else:
    print('Target 1 NOT FOUND')
    
if target2 in content:
    content = content.replace(target2, replace2)
    print('Target 2 replaced')
else:
    print('Target 2 NOT FOUND')

with open('d:/Project/FDA detectionV2/FDA-Detection/backend/app/api/endpoints.py', 'w', encoding='utf-8') as f:
    f.write(content)
