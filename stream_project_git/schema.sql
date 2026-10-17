-- 1. 會員帳號 (Account - 強實體)
CREATE TABLE IF NOT EXISTS Account (
    accountId VARCHAR(20) PRIMARY KEY,
    email VARCHAR(128) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    regDate DATE NOT NULL DEFAULT CURRENT_DATE
);

-- 2. 訂閱方案 (Plan - 強實體)
CREATE TABLE IF NOT EXISTS Plan (
    planId VARCHAR(20) PRIMARY KEY,
    planName VARCHAR(64) NOT NULL,
    price INTEGER NOT NULL,
    maxScreens INTEGER NOT NULL
);

-- 3. 影片 (Movie - 強實體)
CREATE TABLE IF NOT EXISTS Movie (
    movieId VARCHAR(20) PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    duration INTEGER NOT NULL,
    rating VARCHAR(20) NOT NULL
);

-- 4. 影片類型 (Genre - 強實體)
CREATE TABLE IF NOT EXISTS Genre (
    genreId VARCHAR(20) PRIMARY KEY,
    genreName VARCHAR(64) NOT NULL,
    description TEXT
);

-- 5. 訂閱紀錄 (Subscription - 強實體)
CREATE TABLE IF NOT EXISTS Subscription (
    subId VARCHAR(20) PRIMARY KEY,
    payDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount INTEGER NOT NULL,
    endDate DATE NOT NULL,
    status VARCHAR(32) NOT NULL,
    accountId VARCHAR(20) NOT NULL,
    planId VARCHAR(20) NOT NULL,
    FOREIGN KEY (accountId) REFERENCES Account(accountId) ON DELETE CASCADE,
    FOREIGN KEY (planId) REFERENCES Plan(planId)
);

-- 6. 個人檔案 (Profile - 弱實體，主鍵為 accountId + profileNo)
CREATE TABLE IF NOT EXISTS Profile (
    accountId VARCHAR(20) NOT NULL,
    profileNo INTEGER NOT NULL,
    profileName VARCHAR(64) NOT NULL,
    isKid BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (accountId, profileNo),
    FOREIGN KEY (accountId) REFERENCES Account(accountId) ON DELETE CASCADE
);

-- 7. 屬於 (Belong - Movie 與 Genre 的 M:N 關係)
CREATE TABLE IF NOT EXISTS Belong (
    movieId VARCHAR(20) NOT NULL,
    genreId VARCHAR(20) NOT NULL,
    PRIMARY KEY (movieId, genreId),
    FOREIGN KEY (movieId) REFERENCES Movie(movieId) ON DELETE CASCADE,
    FOREIGN KEY (genreId) REFERENCES Genre(genreId) ON DELETE CASCADE
);

-- 8. 觀看 (Watch - Profile 與 Movie 的 M:N 關係)
CREATE TABLE IF NOT EXISTS Watch (
    accountId VARCHAR(20) NOT NULL,
    profileNo INTEGER NOT NULL,
    movieId VARCHAR(20) NOT NULL,
    progress INTEGER DEFAULT 0,
    rating INTEGER,
    PRIMARY KEY (accountId, profileNo, movieId),
    FOREIGN KEY (accountId, profileNo) REFERENCES Profile(accountId, profileNo) ON DELETE CASCADE,
    FOREIGN KEY (movieId) REFERENCES Movie(movieId) ON DELETE CASCADE
);

-- 9. 觀看時間 (Watch_Time - Watch 的多值屬性 watchTime：記錄每次觀看的日期與時間點)
CREATE TABLE IF NOT EXISTS Watch_Time (
    accountId VARCHAR(20) NOT NULL,
    profileNo INTEGER NOT NULL,
    movieId VARCHAR(20) NOT NULL,
    watchTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (accountId, profileNo, movieId, watchTime),
    FOREIGN KEY (accountId, profileNo, movieId) REFERENCES Watch(accountId, profileNo, movieId) ON DELETE CASCADE
);
