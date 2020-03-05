from datetime import datetime

from AppKit import NSWorkspace

import Quartz.CoreGraphics as CG
import numpy as np
import cv2


def find_window(title):
    window_list = CG.CGWindowListCopyWindowInfo(
        CG.kCGWindowListOptionOnScreenOnly & CG.kCGWindowListExcludeDesktopElements,
        CG.kCGNullWindowID)

    target_window_list = list(filter(lambda w: w.get('kCGWindowName') is not None and w.get('kCGWindowName').find(title) >= 0, window_list))

    return target_window_list


def dump_window_info(window):
    print('%s - %s (PID: %d, WID: %d, Pos: %dx%d, Size: %dx%d)'
          % (
              window['kCGWindowOwnerName'],
              window.get('kCGWindowName', u'(empty)'),
              window['kCGWindowOwnerPID'],
              window['kCGWindowNumber'],
              window['kCGWindowBounds']['X'],
              window['kCGWindowBounds']['Y'],
              window['kCGWindowBounds']['Width'],
              window['kCGWindowBounds']['Height'],
          ))


def get_active_window_info():
    curr_pid = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationProcessIdentifier']
    options = CG.kCGWindowListOptionOnScreenOnly
    window_list = CG.CGWindowListCopyWindowInfo(options, CG.kCGNullWindowID)

    for window in window_list:
        # dump_window_info(window)
        # print(window)
        if curr_pid == window['kCGWindowOwnerPID'] and window.get('kCGWindowName') is not None:
            return window


def capture_window(window_info):
    image = CG.CGWindowListCreateImage(
        CG.CGRectNull,
        CG.CG.kCGWindowListOptionIncludingWindow,
        window_info['kCGWindowNumber'],
        CG.kCGWindowImageBoundsIgnoreFraming | CG.kCGWindowImageBestResolution)
        # CG.kCGWindowImageBoundsIgnoreFraming | CG.kCGWindowImageNominalResolution)


    width = CG.CGImageGetWidth(image)
    height = CG.CGImageGetHeight(image)
    bytesperrow = CG.CGImageGetBytesPerRow(image)

    pixeldata = CG.CGDataProviderCopyData(CG.CGImageGetDataProvider(image))
    image = np.frombuffer(pixeldata, dtype=np.uint8)
    image = image.reshape((height, bytesperrow // 4, 4))
    image = image[:, :width, :]

    return image


def create_template(suit, number):
    im_prefix = 'images/cards_m'
    # 数字の左右の位置調整。pixel
    shift = {
        's': [-1, -1, 0, -1, -1, 0, -1, -1, -1, 0, -1, 0, 0],
        'h': [-1, -1, 0, -1, -1, 0, -1, -1, -1, 0, -1, 0, 0],
        'd': [-1, -1, 0, -1, -1, 0, -1, -1, -1, 0, -1, 0, 0],
        'c': [-1, -1, 0, -1, -1, 0, -1, -1, -1, 0, -1, 0, 0],
    }
    # space = {'s': 4, 'h': 6, 'd': 4, 'c': 2}
    space = {'s': 8, 'h': 10, 'd': 6, 'c': 8}
    color = {'s': 'b', 'h': 'r', 'd': 'r', 'c': 'b'}
    n = cv2.imread('{}/{}{}.png'.format(im_prefix, number, color[suit]))
    s = cv2.imread('{}/{}.png'.format(im_prefix, suit))[:-8, :]

    s_width = s.shape[1]
    s_height = s.shape[0]
    # 番号部は位置調整用の余白を2px追加
    template_width = max(s.shape[1], n.shape[1] + 2)

    n_back = np.full((n.shape[0], template_width, 3), 255)
    s_back = np.full((s_height, template_width, 3), 255)
    spacer = np.full((space.get(suit), template_width, 3), 255)

    n_width = n.shape[1]
    n_left_margin = int((n_back.shape[1] - n_width)/2) + shift[suit][number - 1]
    s_left_margin = int((s_back.shape[1] - s_width)/2)

    n_back[:, n_left_margin:n_left_margin + n.shape[1]] = n
    s_back[:, s_left_margin:s_left_margin + s.shape[1]] = s

    n_and_s = np.vstack((n_back, spacer, s_back)).astype('u1')
    template = cv2.cvtColor(n_and_s, cv2.COLOR_BGR2GRAY)

    return template

    # downscale
    # scaled = cv2.resize(template, (int(n_and_s.shape[1]*3/5), int(n_and_s.shape[0]*3/5)), interpolation=cv2.INTER_AREA)
    # return scaled


if __name__ == '__main__':
    # out_image = cv2.imread('images_for_test/poker.png')

    active_window_info = get_active_window_info()

    if active_window_info['kCGWindowOwnerName'] != 'PokerStars':
        print('Active window is not PokerStars. exited.')
        exit(0)

    out_image = capture_window(active_window_info)

    # 画面の真ん中あたりを取得
    hh, ww = out_image.shape[:-1]
    ww = int(ww/3)
    hh = int(hh/3)

    out_image = out_image[hh:hh+int(hh * 1.1), ww:ww+ww]
    window_image = cv2.cvtColor(out_image, cv2.COLOR_BGR2GRAY)

    # cv2.imwrite(f'out_{int(datetime.now().timestamp())}.png', out_image)

    # # scale
    # target_width = 2192
    # scale = target_width/out_image.shape[1]
    # width = int(out_image.shape[1] * scale)
    # height = int(out_image.shape[0] * scale)
    # dim = (width, height)
    #
    # out_image = cv2.resize(out_image, dim, interpolation=cv2.INTER_AREA)
    # window_image = cv2.resize(window_image, dim, interpolation=cv2.INTER_AREA)

    detected_cards = []

    for s in 'shdc':
        for i in range(1,14):
            template = create_template(s, i)
            result = cv2.matchTemplate(window_image, template, cv2.TM_CCOEFF_NORMED)

            # cv2.imwrite('template_{}_{}.png'.format(i, s), template)

            # 検出結果から検出領域の位置を取得
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            # print('s={}, i={}'.format(s, i))
            # print('min_val={:.3f}, max_val={:.3f}, min_loc={}, max_loc={}'.format(min_val, max_val, min_loc, max_loc))

            if max_val < 0.95:
                continue

            detected_cards.append([s, i, max_val])

            # top_left = max_loc
            # w, h = template.shape[::-1]
            # bottom_right = (top_left[0] + w, top_left[1] + h)
            #
            # cv2.rectangle(out_image, top_left, bottom_right, (255, 0, 0), 2)

    suit_dict = {'s': 'S', 'h': 'H', 'd': 'D', 'c': 'C'}
    num_dict = {1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K'}

    num_cards = len(detected_cards)
    print('Number of cards: {}'.format(num_cards))

    #  pre-flop, flop, turn, river
    if num_cards == 0:
        print('Stage: --')
    elif 1 <= num_cards <= 2:
        print('Stage: Pre-Flop')
    elif 3 <= num_cards <= 5:
        print('Stage: Flop')
    elif num_cards == 6:
        print('Stage: Turn')
    elif num_cards == 7:
        print('Stage: River')

    message = '\n'.join(map(lambda x: '{}-{},\tsimilarity={:.3f}'. format(num_dict[x[1]], suit_dict.get(x[0]), x[2]), detected_cards))
    print(message)

    # cv2.imwrite("result2.png", out_image)
    # cv2.imwrite(f'out_{int(datetime.now().timestamp())}.png', out_image)
