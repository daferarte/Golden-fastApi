# app/services/fingerprint.py

import cv2
import numpy as np

class Fingerprint:
    def __init__(self, data):
        self.minutiae = self._extract_minutiae(data)
        self.image = self._create_image_from_minutiae()
        self.keypoints = None
        self.descriptors = None
        if self.image is not None:
            self._extract_features()

    def _extract_minutiae(self, data):
        points = []
        offset = 6
        while offset + 2 < len(data):
            x = data[offset]
            y = data[offset + 1]
            if x != 0 or y != 0:
                points.append((x, y))
            offset += 3
        return points

    def _create_image_from_minutiae(self):
        if not self.minutiae:
            return None
        
        img_height = 288
        img_width = 256
        image = np.zeros((img_height, img_width), dtype=np.uint8)
        
        for x, y in self.minutiae:
            if x < img_width and y < img_height:
                 cv2.circle(image, center=(x, y), radius=2, color=255, thickness=-1)
                 
        return image

    def _extract_features(self):
        orb = cv2.ORB_create(nfeatures=500)
        self.keypoints, self.descriptors = orb.detectAndCompute(self.image, None)

    def compare(self, other_fp):
        if self.descriptors is None or other_fp.descriptors is None:
            return 0
        
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(self.descriptors, other_fp.descriptors)
        
        # --- PARÁMETRO MÁS ESTRICTO ---
        # Antes: m.distance < 70
        # Ahora, las características deben ser mucho más similares para contar como una buena coincidencia.
        good_matches = [m for m in matches if m.distance < 60]
        
        total_features = min(len(self.descriptors), len(other_fp.descriptors))
        if total_features == 0:
            return 0
            
        score = (len(good_matches) / total_features) * 100
        return score
