import cv2
import pytesseract
import re


class KmExtractor:
    def __init__(self, video_path):
        self.video_path = video_path

        self.config = "--psm 6 --oem 1"

    def get_roi(self, frame):
        h, w = frame.shape[:2]

        return frame[0:int(h * 0.15), :]

    def preprocess(self, roi):
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        _, thresh = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        return thresh

    def ocr_multi(self, frame):
        if frame is None:
            return ""

        roi = self.get_roi(frame)

        if roi is None or roi.size == 0:
            return ""

        img = self.preprocess(roi)

        text = pytesseract.image_to_string(
            img,
            lang="rus+eng",
            config=self.config
        )

        return re.sub(r"\s+", " ", text.strip())

    def extract_kilometer(self, text):
        if not text:
            return None

        text = text.lower()
        text = text.replace("km", "км").replace("xm", "км")

        clean = re.sub(r"[^0-9.,км\s]", " ", text)
        clean = re.sub(r"\s+", " ", clean)

        match = re.search(r"([0-9]+[.,]?[0-9]*)\s*км", clean)
        if match:
            return match.group(1).replace(",", ".")

        glued = clean.replace(" ", "")

        match2 = re.search(r"(\d+[.,]?\d*)км", glued)
        if match2:
            return match2.group(1).replace(",", ".")

        match3 = re.search(r"(\d+[.,]\d{2,4})", glued)
        if match3:
            return match3.group(1).replace(",", ".")

        return None