CREATE TABLE IF NOT EXISTS counts (
    id INT PRIMARY KEY,
    message TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    client_ip TEXT NOT NULL
);

-- Ensure mooindagcounter user has full permissions
GRANT ALL PRIVILEGES ON mooindagcounter.* TO 'mooindagcounter'@'%';
FLUSH PRIVILEGES;
