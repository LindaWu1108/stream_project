-- 1. 訂閱方案 (Plan) - 包含基本、標準、高級，以及尚未被選擇的 P04（體現 Plan 部分參與）
INSERT INTO Plan (planId, planName, price, maxScreens) VALUES
('P01', '基本', 270, 1),
('P02', '標準', 330, 2),
('P03', '高級', 390, 4),
('P04', '學生單人', 190, 1)
ON CONFLICT (planId) DO NOTHING;

-- 2. 會員帳號 (Account)
INSERT INTO Account (accountId, email, password, regDate) VALUES
('A001', 'family@example.com', '1234', '2026-01-15'),
('A002', 'linda@example.com', '1234', '2026-03-20'),
('A003', 'admin@example.com', 'admin', '2026-01-01')
ON CONFLICT (accountId) DO NOTHING;

-- 3. 訂閱紀錄 (Subscription) - A001 有兩筆續訂紀錄（體現 1:N 關係），管理員 A003 不會有訂閱消費
INSERT INTO Subscription (subId, payDate, amount, endDate, status, accountId, planId) VALUES
('S001', '2026-09-01 10:00:00', 390, '2026-10-01', '已到期', 'A001', 'P03'),
('S002', '2026-10-01 10:05:00', 390, '2026-11-01', '使用中', 'A001', 'P03'),
('S003', '2026-10-05 14:20:00', 330, '2026-11-05', '使用中', 'A002', 'P02')
ON CONFLICT (subId) DO NOTHING;

-- 4. 個人檔案 (Profile - 弱實體：爸爸、媽媽、小明[兒童模式])
INSERT INTO Profile (accountId, profileNo, profileName, isKid) VALUES
('A001', 1, '爸爸', FALSE),
('A001', 2, '媽媽', FALSE),
('A001', 3, '小明', TRUE),
('A002', 1, 'Linda', FALSE),
('A002', 2, '小美', FALSE),
('A003', 1, '系統管理員', FALSE)
ON CONFLICT (accountId, profileNo) DO NOTHING;

-- 5. 影片類型 (Genre)
INSERT INTO Genre (genreId, genreName, description) VALUES
('G01', '動作', '緊張刺激的動作與冒險場面'),
('G02', '科幻', '未來科技、太空探索與跨時空想像'),
('G03', '愛情', '浪漫感人的情感與家庭故事'),
('G04', '恐怖', '驚悚懸疑與超自然現象'),
('G05', '動畫', '適合闔家觀賞的動畫作品')
ON CONFLICT (genreId) DO NOTHING;

-- 6. 影片 (Movie) - M006 尚未被觀看（體現 Movie 部分參與 Watch）
INSERT INTO Movie (movieId, title, duration, rating) VALUES
('M001', '星際效應', 169, '保護級'),
('M002', '全面啟動', 148, '輔12'),
('M003', '腦筋急轉彎2', 96, '普遍級'),
('M004', '厲陰宅', 112, '限制級'),
('M005', '關於我和鬼變成家人的那件事', 130, '輔12'),
('M006', '沙丘：第二部', 166, '保護級')
ON CONFLICT (movieId) DO NOTHING;

-- 7. 屬於 (Belong - Movie 與 Genre 的 M:N 關係)
INSERT INTO Belong (movieId, genreId) VALUES
('M001', 'G01'),
('M001', 'G02'),
('M002', 'G01'),
('M002', 'G02'),
('M003', 'G05'),
('M004', 'G04'),
('M005', 'G01'),
('M005', 'G03'),
('M006', 'G01'),
('M006', 'G02')
ON CONFLICT (movieId, genreId) DO NOTHING;

-- 8. 觀看 (Watch - Profile 與 Movie 的 M:N 關係，含關係屬性 progress, rating)
-- 包含系統敘述舉例：小明 ('A001', 3) 觀看 星際效應 ('M001') -> progress = 75, rating = 5
INSERT INTO Watch (accountId, profileNo, movieId, progress, rating) VALUES
('A001', 3, 'M001', 75, 5),
('A001', 3, 'M003', 100, 5),
('A001', 1, 'M002', 100, 4),
('A001', 1, 'M004', 50, 3),
('A002', 1, 'M001', 100, 5),
('A002', 1, 'M005', 90, 5)
ON CONFLICT (accountId, profileNo, movieId) DO NOTHING;

-- 9. 觀看時間點 (Watch_Time - 多值屬性 watchTime，記錄每次觀看的「年-月-日 時:分:秒」時間點)
INSERT INTO Watch_Time (accountId, profileNo, movieId, watchTime) VALUES
('A001', 3, 'M001', '2026-10-10 19:30:00'),
('A001', 3, 'M001', '2026-10-12 20:15:00'),
('A001', 3, 'M003', '2026-10-14 18:00:00'),
('A001', 1, 'M002', '2026-10-11 22:10:00'),
('A001', 1, 'M004', '2026-10-15 23:05:00'),
('A002', 1, 'M001', '2026-10-08 21:00:00'),
('A002', 1, 'M005', '2026-10-16 20:45:00')
ON CONFLICT (accountId, profileNo, movieId, watchTime) DO NOTHING;
