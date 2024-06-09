# 載入模組
import pygame
import os
import time
import random
from PIL import Image, ImageFilter
pygame.font.init()

# 初始遊戲設置
WIDTH, HEIGHT = 750, 750  # Note: 這邊的 X 是由左往右增加，但 Y 應該是由上往下增加 (整個顛倒)
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
parent_dir = os.path.dirname(__file__)
os.chdir(parent_dir)

# 載入圖片
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "villian1.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "villian3.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "villian2.png"))
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))
heal = pygame.image.load(os.path.join("assets","heal.png"))
HEADER = pygame.image.load(os.path.join("assets","header.png"))
header_w, header_h = HEADER.get_width(), HEADER.get_height()
HEADER = pygame.transform.scale(HEADER, (WIDTH * 0.85, WIDTH * 0.75 * header_h / header_w))
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))


# 每個角色的class
class Laser:
    def __init__(self, x, y, img):  # 初始化雷射子彈的重要特徵
        self.x = x  # 水平位置
        self.y = y  # 垂直位置
        self.img = img  # 圖檔
        self.mask = pygame.mask.from_surface(self.img)  # 圖形遮罩，用於碰撞偵測

    def draw(self, window):  # 在 Surface 上繪製子彈位置 (Surface 物件 = WIN)
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):  # 移動子彈垂直位置
        self.y += vel

    def off_screen(self, height):
    # 判斷子彈是否超出視窗，左判定式代表子彈是否完全出下界，右判定式代表子彈是否出上界
        return self.y < -self.img.get_height() or self.y > height

    def collision(self, obj):  # 利用下面的 collide 函數判定物件之間是否碰撞 (精確至 1 pixel)
        return collide(self, obj)


class Blood:
    def __init__(self, x, y, img):  # 初始化回血包的重要特徵
        self.x = x  # 水平位置
        self.y = y  # 垂直位置
        self.img = img  # 圖檔
        self.mask = pygame.mask.from_surface(self.img)  # 圖形遮罩，用於碰撞偵測

    def draw(self, window):  # 在 Surface 上繪製子彈位置 (Surface 物件 = WIN)
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):  # 移動子彈垂直位置
        self.y += vel

    def collision(self, obj):  # 利用下面的 collide 函數判定物件之間是否碰撞 (精確至 1 pixel)
        return collide(self, obj)


class Ship:
    COOLDOWN = 30  # Ship 物件的共享 Static Variable
    def __init__(self, x, y, health=100):  # 初始化戰鬥機 (不分敵我) 都共同持有的重要特徵
        self.x = x  # 水平位置
        self.y = y  # 垂直位置
        self.health = health  # 生命值
        self.ship_img = None  # 預設為空，因敵我有差
        self.laser_img = None  # 預設為空，因敵我有差
        self.lasers = []  # 初始化一個空清單存放該單位的子彈物件
        self.cool_down_counter = 0  # 應該是專屬敵機的特徵，先初始化後續供函數使用

    def draw(self, window):  # 在 Surface 上繪製戰鬥機及其子彈位置 (Surface 物件 = WIN)
        window.blit(self.ship_img, (self.x, self.y))  # 先畫戰鬥機
        for laser in self.lasers:  # 再把所有子彈畫上去
            laser.draw(window)

    def move_lasers(self, vel, obj):  # 移動子彈，且碰到對方後使之扣血
        self.cooldown()  # 單位冷卻時間會變成 either 0 or 1
        for laser in self.lasers:
            laser.move(vel)  # 移動該戰鬥機所有子彈
            if laser.off_screen(HEIGHT):  # 若子彈超出邊界，從該戰鬥機的子彈清單中刪除該子彈
                self.lasers.remove(laser)
            elif laser.collision(obj):  # 跟子彈接觸到的那個單位減10生命，並將該子彈刪除
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):  # 專屬敵機的函數，用來迭代發射間隔時間，最長 30 單位時間
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):  # 當單位的 cooldown 參數為 0，則產生並發射子彈
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):  # 回傳物件寬度
        return self.ship_img.get_width()

    def get_height(self):  # 回傳物件高度
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):  # 定義玩家戰鬥機的重要特徵
        super().__init__(x, y, health)  # 繼承 Ship 中共享的特徵
        self.ship_img = YELLOW_SPACE_SHIP  # 玩家戰鬥機為黃色機身
        self.laser_img = YELLOW_LASER  # 射出黃色子彈
        self.mask = pygame.mask.from_surface(self.ship_img)  # 創建玩家遮罩，用於碰撞偵測
        self.max_health = health  # 玩家生命值上限為初始給的滿血狀態，用於血條比例

    def move_lasers(self, vel, objs):  # 移動子彈，且碰到敵機直接使之消失
        self.cooldown()  # 單位冷卻時間會變成 either 0 or 1
        for laser in self.lasers:
            laser.move(vel)  # 移動該戰鬥機所有子彈
            if laser.off_screen(HEIGHT):  # 若子彈超出邊界，從該戰鬥機的子彈清單中刪除該子彈
                self.lasers.remove(laser)
            else:  # 若未超出邊界，則開始考慮玩家射擊的子彈有無接觸到敵機
                for obj in objs:  # 此處 objs 只所有敵機的清單
                    if laser.collision(obj):  # 若敵機被子彈接觸到，則敵機倒地並移除
                        objs.remove(obj)
                        if laser in self.lasers:  # 該子彈若屬於玩家，也從玩家的子彈清單中移除
                            self.lasers.remove(laser)

    def draw(self, window):  # 在 Surface 上繪製戰鬥機及其子彈位置 (Surface 物件 = WIN)
        super().draw(window)  # 繼承 Ship 物件所有 Draw 函數指令
        self.healthbar(window)  # 再繪製玩家的血條 (玩家專屬)

    def healthbar(self, window):  # 紅條畫滿，當背景用；律條跟生命值成比例，疊在紅色上
        pygame.draw.rect(window, (255,0,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0,255,0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health/self.max_health), 10))


class Enemy(Ship):
    COLOR_MAP = {  # Static Variable，隨機給所有敵機不同配色用的 map
                "red": (RED_SPACE_SHIP, RED_LASER),
                "green": (GREEN_SPACE_SHIP, GREEN_LASER),
                "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
                }

    def __init__(self, x, y, color, health=100):  # 定義敵機的重要特徵
        super().__init__(x, y, health)  # 繼承 Ship 中共享的特徵
        self.ship_img, self.laser_img = self.COLOR_MAP[color]  # 隨機生成一色
        self.mask = pygame.mask.from_surface(self.ship_img)  # 創建敵機遮罩，用於碰撞偵測

    def move(self, vel):  # 移動敵機垂直位置 (每次一單位向下移動)
        self.y += vel

    def shoot(self):  # 當單位的 cooldown 參數為 0，則產生並發射子彈
        if self.cool_down_counter == 0:
            laser = Laser(self.x-20, self.y, self.laser_img)
            # 初始化子彈設計在敵機左方 20 單位射出。我猜是因為程式辨認物件的原點在右側，或是敵機上下左右顛倒
            self.lasers.append(laser)
            self.cool_down_counter = 1


# 碰撞的函式(回傳是否碰撞 T/F)
def collide(obj1, obj2):  # 通常 obj1 為主體，obj2 為物件。被拿來偵測補血包、子彈、敵機的碰撞
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


# 模糊背景函示
def blur_surface(surface, rect, radius):
    ## 提取指定區域
    sub_surface = surface.subsurface(rect).copy()
    ## 將該區域轉換為 PIL 圖片進行模糊處理
    pil_image = Image.frombytes("RGBA", sub_surface.get_size(), pygame.image.tostring(sub_surface, "RGBA"))
    pil_image = pil_image.filter(ImageFilter.GaussianBlur(radius))
    ## 將模糊處理後的圖片轉回 Pygame 圖片
    blurred_sub_surface = pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode)
    return blurred_sub_surface


# 主遊戲的函式
def main():
    ## 整個遊戲的參數
    run = True  # 迴圈 flag
    paused = False  # 暫停 flag
    FPS = 50  # 遊戲幀數
    level = 0  # 從 0 開始，最高到 Level 5 玩家贏。
    lives = 5  # 5 條命，一架敵機衝線算一條
    main_font = pygame.font.SysFont("impact", 50)  # 主要字型、字體，例如左右上角的提示。
    lost_font = pygame.font.SysFont("impact", 60)  # Game over 的字型、字體。
    win_font = pygame.font.SysFont("impact", 70)  # win 的字型、字體。
    ## 遊戲內物件的參數
    enemies = []  # 初始化敵機清單
    bloods = []  # 初始化補血包清單
    wave_length = 5  # 敵機數量 (隨 level 增加遞增)
    enemy_vel = 1  # 敵機移動速度
    blood_vel = 1  # 補血包移動速度
    player_vel = 5  # 玩家移動速度 (也是單位移動距離)
    laser_vel = 5  # 子彈移動速度
    ## 玩家的參數
    player = Player(300, 630)  # 初始化玩家的戰鬥機物件
    ## 遊戲內時間
    clock = pygame.time.Clock()
    ## 判斷輸贏的參數
    lost = False
    lost_count = 0
    win = False
    ## 繪製每一幀的畫面用的函數
    def redraw_window():
        WIN.blit(BG, (0,0))  # 畫背景圖片
        ## draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255,255,255))  # 設置左上角的 Lives 字卡
        level_label = main_font.render(f"Level: {level}", 1, (255,255,255))  # 設置右上角的 Level 字卡
        WIN.blit(lives_label, (10, 10))  # 繪製 Lives 字卡
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))  # 繪製 Level 字卡
        ## 繪製暫停按鈕
        ## 畫上所有敵機、補血包、玩家
        for enemy in enemies:  # 敵機們
            enemy.draw(WIN)
        for blood in bloods:  # 補血包
            blood.draw(WIN)
        player.draw(WIN)  # 玩家
        ## 繪製輸贏字卡
        if win:  # 贏了的情況
            ## 提取並模糊背景
            blurred_rect = blur_surface(WIN, (0, 0, WIDTH, HEIGHT), 5)
            WIN.blit(blurred_rect, (0, 0))
            win_label = win_font.render("Win!!!!", 1,(255,255,255))  # 設置贏家字卡
            WIN.blit(win_label, (WIDTH/2 - win_label.get_width()/2, 350))  # 繪製贏家字卡
        if lost:  # 輸了的情況
            ## 提取並模糊背景
            blurred_rect = blur_surface(WIN, (0, 0, WIDTH, HEIGHT), 5)
            WIN.blit(blurred_rect, (0, 0))
            lost_label = lost_font.render("Game Over!!", 1, (255,255,255))  # 設置輸家字卡
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))  # 繪製輸家字卡
        if paused:
            ## 提取並模糊背景
            blurred_rect = blur_surface(WIN, (0, 0, WIDTH, HEIGHT), 5)
            WIN.blit(blurred_rect, (0, 0))
            pause_label = main_font.render("Paused (Press P to resume)", 1, (255, 255, 255))
            WIN.blit(pause_label, (WIDTH / 2 - pause_label.get_width() / 2, HEIGHT / 2))
        pygame.display.update()  # 用來更新顯示窗口的函式，繪製或改變任何內容後需要用它來顯示變化

    ## 遊戲主循環
    while run:
        clock.tick(FPS)  # 控制幀數在 50 fps
        redraw_window()  # 繪製該循環的畫面
        ## 判斷遊戲輸掉的判斷式
        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1
        ## 這行應該是限制遊玩次數，沒有達到上限就忽略。
        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue
        ## 若贏下這場，則等待三秒後跳出循環重新開始新的一局
        if win :
            time.sleep(3)
            run = False
            continue
        ## 判斷遊戲贏下的判斷式，規則是到 Level 5 贏下來後就贏了這場。
        if len(enemies) == 0:
            if level == 5:  # 贏下 Level 5
                win = True
            else:
                level += 1  # 其他獲勝的狀況，就升級韓增加難度
                wave_length += 5
                for i in range(wave_length):  # 將新增的敵機數量全部初始化
                    enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                    enemies.append(enemy)
        ## 生成補血包的判斷式   
        if random.randrange(0, 15 * 60) == 1:  # 每一幀有 1/900 的機率生出補血包
            blood = Blood(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100), heal)
            bloods.append(blood)
        ## 偵測玩家行為
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                os._exit(0)  # 完全退出，確保在 MacOS 上完全關閉視窗，0 表正常關閉的狀態碼
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # 偵測是否按下 K 以切換遊戲暫停狀態
                    paused = not paused
                if event.key == pygame.K_ESCAPE:  # 偵測是否按下 Esc 以退出遊戲
                    os._exit(0)  # 完全退出，確保在 MacOS 上完全關閉視窗，0 表正常關閉的狀態碼

        # 如果遊戲暫停，浮現一個視窗提示暫停及按 K 繼續
        while paused:
            redraw_window()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    os._exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:  # 偵測是否按下 K 以切換遊戲暫停狀態
                        paused = not paused
                    if event.key == pygame.K_ESCAPE:  # 偵測是否按下 Esc 以退出遊戲
                        os._exit(0)  # 完全退出，確保在 MacOS 上完全關閉視窗，0 表正常關閉的狀態碼
            clock.tick(FPS)  # 估計是讓這個 while 跟遊戲的更新幀數一樣

        ## 偵測玩家的指令 (W, A, S, D, Spc)
        keys = pygame.key.get_pressed()  # 捕捉玩家的鍵盤指令
        if keys[pygame.K_a] and player.x - player_vel > 0: # left (若玩家按 a 及玩家的戰鬥機左一步不會出鏡)
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() < WIDTH: # right (若玩家按 d 及玩家的戰鬥機右一步不會出鏡)
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel > 0: # up (若玩家按 w 及玩家的戰鬥機上一步不會出鏡)
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < HEIGHT: # down (若玩家按 s 及玩家的戰鬥機下一步不會出鏡)
            player.y += player_vel
        if keys[pygame.K_SPACE]:  # 玩家按空白鍵就是射擊
            player.shoot()  # 證明 Player 繼承了 Ship 的函數
        ## 每一架敵機、該敵機發射的子彈都要向前 (下) 移動一步
        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)
            ## 每架敵機每幀有 1/120 的機率發射子彈
            if random.randrange(0, 2*60) == 1:
                enemy.shoot()
            ## 偵測該架敵機是否與玩家碰撞
            if collide(enemy, player):  # 若是，則玩家扣血，且移除該敵機
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:  # 若敵機衝到下界，則扣一條命，且移除該敵機
                lives -= 1
                enemies.remove(enemy)
        ## 偵測補血包是否接觸到玩家，一次加 20 血
        for blood in bloods[:]:
            blood.move(blood_vel)
            if blood.collision(player):
                player.health += 20
                if player.health > player.max_health:  # 玩家補到滿血後，補血包就沒效果
                    player.health = player.max_health
                bloods.remove(blood)
            elif blood.y > HEIGHT:  # 當補血包到下界後就移除
                bloods.remove(blood)
        ## 玩家的子彈們也要向上移動一步
        player.move_lasers(-laser_vel, enemies)


# 操作介紹  
def main_menu():
    title_font = pygame.font.SysFont("impact", 20)  # 操作指引的主要字型、字體。
    run = True  # 迭代操作指引的 flag
    enlarge_factor = 1.5  # 初始化小動畫的放大係數
    decreasing = True  # 小動畫在縮小還是放大的 flag

    while run:
        ## 繪製背景圖片
        WIN.blit(BG, (0, 0))
        ## 繪製遊戲標題
        scaled_width = int(HEADER.get_width() * enlarge_factor)  # 根據放大係數計算新的寬度
        scaled_height = int(HEADER.get_height() * enlarge_factor)  # 根據放大係數計算新的高度
        scaled_header = pygame.transform.scale(HEADER, (scaled_width, scaled_height))
        WIN.blit(scaled_header, ((WIDTH - scaled_width) // 2, HEIGHT // 2 - scaled_height))
        ## 更新放大係數
        if decreasing:
            enlarge_factor -= 0.005
            if enlarge_factor <= 0.5:
                decreasing = False
        else:
            enlarge_factor += 0.005
            if enlarge_factor >= 1.5:
                decreasing = True
        ## 設置所有操作指引的字卡
        title_labelw = title_font.render("Press W to go up", 1, (255,255,255))
        title_labela = title_font.render("Press S to go down", 1, (255,255,255))
        title_labels = title_font.render("Press A to go left", 1, (255,255,255))
        title_labeld = title_font.render("Press D to go right", 1, (255,255,255))
        title_labelSpc = title_font.render("Press Space to shoot", 1, (255,255,255))
        title_labelPos = title_font.render("Press P to pause", 1, (255,255,255))
        title_labelCls = title_font.render("Press Esc to leave", 1, (255,255,255))
        ## 集合起來
        labels = [title_labelw, title_labela, title_labels, title_labeld, title_labelSpc, title_labelPos, title_labelCls]

        ## 設置矩形框位置和大小
        total_height = len(labels) * title_font.get_height()  # 計算總高度
        box_width = 220
        box_height = total_height + 20
        box_x = (WIDTH - box_width) // 2
        box_y = HEIGHT // 2 + 20

        ## 提取並模糊邊框內的區域
        blurred_rect = blur_surface(WIN, (box_x, box_y, box_width, box_height), 10)
        WIN.blit(blurred_rect, (box_x, box_y))

        ## 繪製方框背景
        pygame.draw.rect(WIN, (165, 167, 167), (box_x, box_y, box_width, box_height), 3)

        ## 繪製所有操作指引的字卡
        for i, label in enumerate(labels):
            label_rect = label.get_rect(center=(WIDTH // 2, box_y + 20 + i * 25))
            WIN.blit(label, label_rect)

        pygame.display.update()  # 用來更新顯示窗口的函式，繪製或改變任何內容後需要用它來顯示變化
        for event in pygame.event.get():  # 獲取所有用戶行為事件 (輸入、點擊、系統事件)
            if event.type == pygame.QUIT:
                run = False  # 當出現了用戶行為的窗口關閉事件，則停止循環
            elif event.type == pygame.MOUSEBUTTONDOWN:
                main()  # 當出現了滑鼠按下事件，開始遊戲主程式
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False  # 當出現了用戶按下 Esc 的行為，則停止循環
    pygame.quit()  # 退出遊戲物件 (確保資源正確釋放)
    os._exit(0)  # 完全退出，確保在 MacOS 上完全關閉視窗，0 表正常關閉的狀態碼


# 執行函數
main_menu()
