import cv2
import json
import os
import argparse

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def pick_first_frame(cap):
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Cannot read first frame from video/camera.")
    return frame

def main():
    parser = argparse.ArgumentParser(description="ROI Picker (click points on the frame)")
    parser.add_argument("--video", type=str, default="data/sample_track_video.mp4", help="Path to input video")
    parser.add_argument("--camera", action="store_true", help="Use webcam instead of video file")
    parser.add_argument("--camera_index", type=int, default=0, help="Webcam index")
    parser.add_argument("--out", type=str, default="outputs/roi_polygon.json", help="Output ROI polygon JSON file")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.camera_index if args.camera else args.video)
    if not cap.isOpened():
        raise RuntimeError("Cannot open input (video/camera). Check path or camera index.")

    frame = pick_first_frame(cap)
    cap.release()

    points = []
    window_name = "ROI Picker - Click points (S=save, U=undo, R=reset, Q/ESC=quit)"

    def redraw(img):
        display = img.copy()
        for i, (x, y) in enumerate(points):
            cv2.circle(display, (x, y), 6, (0, 255, 255), -1)
            cv2.putText(display, str(i+1), (x+8, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if len(points) >= 2:
            for i in range(len(points) - 1):
                cv2.line(display, points[i], points[i+1], (255, 180, 0), 2)
        if len(points) >= 3:
            cv2.line(display, points[-1], points[0], (255, 180, 0), 2)

        cv2.putText(display, "Click points around the critical trackside/platform zone.", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, "Keys: S=save | U=undo | R=reset | Q/ESC=quit", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return display

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, on_mouse)

    while True:
        display = redraw(frame)
        cv2.imshow(window_name, display)
        key = cv2.waitKey(10) & 0xFF

        if key in (ord('s'), ord('S')):
            if len(points) < 3:
                print("Need at least 3 points to form a polygon ROI.")
                continue
            ensure_dir(args.out)
            payload = {"roi_polygon": points}
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            print("Saved ROI polygon to:", args.out)
            print("ROI_POLYGON =", points)
            break

        if key in (ord('u'), ord('U')):
            if points:
                points.pop()

        if key in (ord('r'), ord('R')):
            points = []

        if key in (ord('q'), ord('Q'), 27):
            print("Quit without saving.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
