# CyberPanel — Tổng Quan Dự Án

## 1. Giới Thiệu

**CyberPanel** là một **Web Hosting Control Panel** mã nguồn mở, được xây dựng trên nền tảng **OpenLiteSpeed**, giúp đơn giản hóa việc quản lý server và web hosting. Dự án cung cấp giải pháp tích hợp cho nhà cung cấp hosting và quản trị viên hệ thống để quản lý website, domain, email, database, DNS và nhiều dịch vụ khác trên Linux server.

- **Giấy phép:** GNU General Public License v3 (GPL-3)
- **Phiên bản hiện tại:** 2.4 (Build 5)
- **Ngôn ngữ chính:** Python
- **Framework:** Django 4.2.14

---

## 2. Công Nghệ Sử Dụng (Tech Stack)

### Core Framework
| Thành phần | Phiên bản | Mục đích |
|---|---|---|
| Python | 3.6+ | Ngôn ngữ chính |
| Django | 4.2.14 | Web framework |
| FastAPI | 0.115.12 | SSH server WebSocket |
| MySQL/MariaDB | — | Database chính (dual-database: `default` + `rootdb`) |

### Web Server
- **OpenLiteSpeed / LiteSpeed Web Server** — Application server chính
- **Apache Controller** — Hỗ trợ tương thích Apache

### Async & WebSocket
| Thư viện | Phiên bản | Mục đích |
|---|---|---|
| asyncssh | 2.21.0 | SSH protocol async |
| websockets | 15.0.1 | WebSocket connections |
| Tornado | 6.4.1 | Async event handling |
| uvicorn | 0.34.2 | ASGI server cho FastAPI |

### Bảo mật & Xác thực
| Thư viện | Phiên bản | Mục đích |
|---|---|---|
| bcrypt | 4.2.0 | Password hashing |
| cryptography | 43.0.0 | Encryption |
| pyOpenSSL | 24.2.1 | SSL/TLS management |
| pyotp | — | Two-factor authentication (OTP) |
| python-jose | 3.4.0 | JWT token handling |
| paramiko | 3.4.1 | SSH protocol client |

### Cloud & Backup
| Thư viện | Phiên bản | Mục đích |
|---|---|---|
| boto3 | 1.34.153 | AWS S3 integration |
| cloudflare | 2.20.0 | CloudFlare DNS/CDN |
| google-api-python-client | 2.139.0 | Google Drive/Cloud |
| docker | 7.1.0 | Docker container management |

### DNS & Network
- **PowerDNS** — Lightweight DNS server tích hợp
- **py3dns 4.0.2** — DNS utilities
- **tldextract 5.1.2** — Domain name parsing

---

## 3. Kiến Trúc Hệ Thống

### Kiến trúc phân tầng (Layered Architecture)

```
┌──────────────────────────────────────────┐
│   Web UI (Django Templates + JS/CSS)     │
├──────────────────────────────────────────┤
│   REST API / Views (api/, các app views) │
├──────────────────────────────────────────┤
│   Business Logic (plogical/)             │
├──────────────────────────────────────────┤
│   Django ORM / Database Layer            │
├──────────────────────────────────────────┤
│   System Integration (subprocess, OS)    │
└──────────────────────────────────────────┘
```

### Các Design Pattern chính

- **Manager Pattern** — Sử dụng rộng rãi các lớp manager: `virtualHostUtilities`, `vhost`, `WebsiteManager`, `dnsManager`, `backupManager`, `mailserverManager`, `containerManager`, `aiScannerManager`, `phpManager`
- **Utility Pattern** — Các module tiện ích tập trung trong `plogical/`: `mysqlUtilities`, `ftpUtilities`, `sslUtilities`, `dnsUtilities`, `mailUtilities`, `processUtilities`, `CyberCPLogFileWriter`, `letsEncrypt`
- **Multi-Database Router** — Router cho 2 database (`default` và `rootdb`)
- **Middleware Pattern** — `secMiddleware` (security headers), `PhpMyAdminAccessMiddleware` (phpMyAdmin access control), LocaleMiddleware (đa ngôn ngữ)
- **Signal-Based Operations** — Django signals cho model event handling (create, update, delete)

---

## 4. Danh Sách Django Apps (35+ apps)

### Core / Hạ tầng
| App | Mô tả |
|---|---|
| `baseTemplate` | Base template, quản lý version, thông báo, cosmetic settings |
| `loginSystem` | Authentication, ACL (Access Control Lists), quản lý Administrator |
| `api` | REST API endpoints với security validation |
| `CyberCP` | Django project settings, URL routing, middleware |
| `plogical` | Core business logic (60+ module tiện ích) |
| `cli` | Command-line interface (`cyberPanel.py`, `cliParser.py`, `cliLogger.py`) |

### Quản lý Website & Domain
| App | Mô tả |
|---|---|
| `websiteFunctions` | Virtual host management, websites, child domains, alias domains, Docker sites, WordPress |
| `packages` | Hosting packages với resource limits (memory, CPU, I/O, inodes, connections) |
| `CLManager` | CloudLinux integration — resource isolation và CageFS |
| `containerization` | Docker container orchestration |

### Database
| App | Mô tả |
|---|---|
| `databases` | MySQL database creation, users, management |

### Email Services
| App | Mô tả |
|---|---|
| `mailServer` | Email accounts, forwarding, DKIM, catch-all |
| `emailMarketing` | Email marketing (Mautic integration) |
| `emailPremium` | Premium email features |
| `emailDelivery` | Email delivery management |
| `webmail` | Webmail interface (SnappyMail) |
| `postfixSenderPolicy` | SPF — Sender Policy Framework |

### Bảo mật & SSL
| App | Mô tả |
|---|---|
| `manageSSL` | SSL certificate management, Let's Encrypt auto-SSL |
| `firewall` | FirewallD integration, one-click IP blocking |
| `aiScanner` | AI-powered security scanning, malware detection |

### DNS
| App | Mô tả |
|---|---|
| `dns` | PowerDNS integration, zone management, DNSSEC |

### File & FTP
| App | Mô tả |
|---|---|
| `filemanager` | File browser và management interface |
| `ftp` | FTP account management |

### Backup & Recovery
| App | Mô tả |
|---|---|
| `backup` | Backup creation, scheduling, restoration |
| `s3Backups` | AWS S3, DigitalOcean Spaces, MINIO backup destinations |
| `IncBackups` | Incremental backup (Rustic/rclone) |

### Monitoring & Logging
| App | Mô tả |
|---|---|
| `serverStatus` | CPU/RAM/disk monitoring, LiteSpeed monitoring |
| `serverLogs` | System, Apache, LiteSpeed, MySQL logs |

### Performance & Services
| App | Mô tả |
|---|---|
| `tuning` | Server optimization settings |
| `managePHP` | PHP version management (5.6 → 8.5) |
| `manageServices` | System service management |

### Quản lý người dùng
| App | Mô tả |
|---|---|
| `userManagment` | End-user management (reseller/hosting account) với hierarchical access |

### Nâng cao
| App | Mô tả |
|---|---|
| `dockerManager` | Docker site management, command execution |
| `cloudAPI` | Cloud service integrations |
| `highAvailability` | High-availability cluster management |
| `pluginHolder` | Plugin/extension system |
| `pluginInstaller` | Plugin installation management |
| `WebTerminal` | SSH web terminal qua FastAPI WebSocket |

---

## 5. Tính Năng Chính

### Website & Hosting
- **Multi-User Hierarchy** — Admin → Reseller → Hosting Clients với 50+ quyền ACL chi tiết
- **Virtual Host Management** — Tạo website với OpenLiteSpeed/Apache
- **Multi-PHP Support** — PHP 5.6 → 8.5 (cấu hình riêng cho từng domain/child domain)
- **WordPress Manager** — Cài đặt, staging, plugin management
- **Docker Sites** — Deploy website qua Docker container
- **phpMyAdmin** — Giao diện quản lý database tích hợp

### Bảo mật
- **Auto SSL / Let's Encrypt** — Tự động cấp chứng chỉ HTTPS
- **Firewall Integration** — FirewallD với one-click IP blocking
- **AI Security Scanner** — Quét malware bằng AI, theo dõi chi phí và kết quả
- **DNSSEC** — DNS Security Extensions
- **Two-Factor Authentication** — OTP support

### Email
- **Full Email Server** — Postfix SMTP + OpenDKIM
- **Email Forwarding** — Bao gồm pattern/wildcard forwarding
- **Catch-All Email** — Cấu hình per-domain
- **Webmail** — SnappyMail web-based client
- **Email Marketing** — Mautic integration

### Backup
- **Multi-Backend Support** — AWS S3, DigitalOcean Spaces, MINIO, Google Drive, Local
- **Incremental Backup** — Rustic + rclone
- **Scheduled Backup** — Tự động theo lịch
- **Backup Retention** — Chính sách lưu giữ backup

### DNS
- **PowerDNS Integration** — Zone management đầy đủ
- **CloudFlare** — DNS/CDN integration
- **DNSSEC Keys** — Hỗ trợ DNSSEC

### Resource Management
- **cgroups v2** — Giới hạn memory, CPU, I/O per package
- **Disk Quotas** — Quota per website/user
- **Bandwidth Tracking** — Theo dõi và reset hàng tháng
- **Inode Limits** — Giới hạn số lượng file

---

## 6. REST API

### Cấu trúc
- **Base Path:** `/api/`
- **Authentication:** API key per administrator + token-based (bcrypt hashing)
- **Format:** JSON request/response
- **CSRF:** Exempt cho programmatic access

### Endpoint chính
| Endpoint | Mô tả |
|---|---|
| `POST /api/verifyConn` | Xác thực kết nối (username/password) |
| Các endpoint khác | Theo từng app (website, database, email, DNS, ...) |

### Bảo mật API
- Phát hiện pattern nguy hiểm trong input: `;`, `&&`, `||`, `` ` ``, `$()`, `../`, `<script>`, `eval`, `exec`, `system`, `shell_exec`
- HTTP status codes: 401, 403, 404, 405, 500
- JWT support cho FastAPI endpoints

---

## 7. Database Models — Tổng Quan

### User & Access Control
- **Administrator** — Admin users (email, tên, ACL, API flag, token)
- **ACL** — 50+ quyền chi tiết (tạo/xóa/sửa website, database, email, DNS, backup, SSL...)

### Website & Domain
- **Websites** — Domain, admin owner, package, PHP version, SSL state
- **ChildDomains** — Subdomain riêng PHP version và SSL
- **aliasDomains** — Domain aliases
- **GitLogs** — Theo dõi thay đổi website

### Package & Resource
- **Package** — Disk space, bandwidth, email accounts, databases, FTP accounts, resource limits
- **CLPackages** — CloudLinux-specific resource limits

### Email
- **EUsers** — Email users
- **Domains** — Email domains gắn với websites
- **Forwardings** — Email forwarding rules
- **CatchAllEmail** — Catch-all per domain
- **PatternForwarding** — Wildcard/regex forwarding

### DNS (PowerDNS)
- **Domains** — DNS zones (NATIVE, MASTER, SLAVE)
- **Records** — DNS records (A, AAAA, CNAME, MX, TXT, ...)
- **Cryptokeys** — DNSSEC keys

### Databases
- **Databases** — MySQL databases gắn với websites
- **DatabasesUsers** — Database users
- **GlobalUserDB** — Global database credentials

### Backup
- **BackupJob + BackupJobLogs** — Theo dõi backup execution
- **GDrive + GDriveSites** — Google Drive backup
- **BackupPlan** — Lịch backup (S3/DO/MINIO)
- **NormalBackupDests** — Backup destinations

### FTP
- **Users** — FTP accounts gắn với websites, có quotas

### Security
- **FirewallRules** — Rule firewall (name, protocol, port, IP)
- **AIScannerSettings** — AI scanner config (API keys, balance)
- **ScanHistory** — Lịch sử scan (type, status, cost, findings)

---

## 8. Cài Đặt & Triển Khai

### Hệ điều hành hỗ trợ
| OS | Phiên bản |
|---|---|
| Ubuntu | 24.04.3, 22.04, 20.04 |
| Debian | 13, 12, 11 |
| AlmaLinux | 10, 9, 8 |
| RockyLinux | 9, 8 |
| RHEL | 9, 8 |
| CloudLinux | 8 |
| CentOS | 9 |
| openEuler | 20.03, 22.03 |

### Cài đặt nhanh
```bash
curl https://cyberpanel.sh | bash
```

### Quy trình cài đặt
1. `install.sh` — Phát hiện OS và bootstrap
2. `cyberpanel.sh` — Script cài đặt chính với logging chi tiết
3. Tự động tạo Python virtual environment tại `/usr/local/CyberCP`
4. Cài đặt OpenLiteSpeed, MySQL/MariaDB, Let's Encrypt, Postfix, PowerDNS, phpMyAdmin

### Đường dẫn cài đặt
| Đường dẫn | Mô tả |
|---|---|
| `/usr/local/CyberCP` | Application root |
| `/usr/local/CyberCP/bin/python` | Virtual environment Python |
| `/usr/local/CyberCP/manage.py` | Django management |
| `/usr/local/CyberCP/public/static/` | Static files |
| `/var/log/cyberpanel/` | Log files |

### Nâng cấp
- `upgrade.sh` — Thu thập static files và restart services
- `cyberpanel_upgrade.sh` — Nâng cấp toàn diện
- `preUpgrade.sh` — Kiểm tra trước nâng cấp

---

## 9. Testing

### OLS Feature Tests (128 tests)
Vị trí: `tests/ols_feature_tests.sh` và `tests/ols_test_setup.sh`

**Phase 1 (56 tests):** Live environment validation
- Binary integrity, Auto-SSL, Let's Encrypt, SSL listener, HTTPS/HTTP, .htaccess, VHost, PHP config

**Phase 2 (72 tests):** ReadApacheConf processing
- Include directives, Listener creation, ProxyPass, VHost creation, SSL deduplication, PHP detection, Process health, Graceful restart

### Unit & Integration Tests
- Mỗi app có `tests.py` sử dụng Django test framework
- `test_api_endpoint.py` — API endpoint testing
- `test_backup_compatibility.py` — Backup system testing
- `test_debian13_support.sh` — OS compatibility testing
- `test_firewall_blocking.py` — Firewall testing

---

## 10. Hệ Thống Plugin

### Kiến trúc
- **Plugin Holder:** `pluginHolder/` — Plugin registry
- **Signals-Based:** Django signals cho plugin hooks
- **Plugin Manager per App:** Mỗi app chính có `pluginManager.py`
  - `websiteFunctions/pluginManager.py`
  - `firewall/pluginManager.py`
  - `dns/pluginManager.py`
  - `backup/pluginManager.py`
  - `mailServer/pluginManager.py`
  - `databases/pluginManager.py`
  - `emailMarketing/pluginManager.py`
- **Global Plugin Manager:** `plogical/pluginManagerGlobal.py`
- **Example Plugin:** `examplePlugin/` — Template plugin mẫu

### Khả năng Plugin
- Website lifecycle hooks (create, delete, modify)
- Firewall rule management
- DNS zone operations
- Backup scheduling
- Email service integration
- Database operations

---

## 11. Bảo Mật

### Xác thực & Phân quyền
- **Three-Tier User Hierarchy:** Admin → Reseller → Hosting Clients
- **ACL System:** 50+ quyền chi tiết
- **bcrypt** password hashing
- **Token-based** authentication
- **Two-Factor** authentication (OTP)

### API Security
- Phát hiện pattern nguy hiểm trong input
- CSRF protection
- HTTP status code error handling
- API key per administrator

### SSL/TLS
- Let's Encrypt auto-provisioning
- Custom SSL certificate support
- SSL listener auto-mapping
- Certificate renewal automation
- DNSSEC key management

### System-Level
- System user isolation per website
- File permissions management (711 home, 750 public_html)
- Chroot/CageFS (CloudLinux)
- Security middleware
- FirewallD integration

---

## 12. Cấu Trúc Thư Mục

```
cyberpanel/
├── CyberCP/                     # Django project settings, urls, middleware
├── plogical/                    # Core business logic (60+ modules)
│   ├── virtualHostUtilities.py
│   ├── vhost.py
│   ├── mysqlUtilities.py
│   ├── mailUtilities.py
│   ├── sslUtilities.py
│   ├── letsEncrypt.py
│   ├── processUtilities.py
│   ├── CyberCPLogFileWriter.py
│   └── ...
├── loginSystem/                 # Authentication & ACL
├── websiteFunctions/            # Website & domain management
├── packages/                    # Hosting packages
├── databases/                   # MySQL management
├── mailServer/                  # Email services
├── dns/                         # PowerDNS integration
├── firewall/                    # FirewallD integration
├── backup/                      # Backup & restore
├── s3Backups/                   # S3/DO/MINIO backups
├── IncBackups/                  # Incremental backups
├── manageSSL/                   # SSL management
├── managePHP/                   # PHP version management
├── manageServices/              # System services
├── filemanager/                 # File browser
├── ftp/                         # FTP management
├── serverStatus/                # System monitoring
├── serverLogs/                  # Log viewer
├── tuning/                      # Performance tuning
├── userManagment/               # User management
├── dockerManager/               # Docker management
├── containerization/            # Container orchestration
├── aiScanner/                   # AI security scanner
├── cloudAPI/                    # Cloud integrations
├── highAvailability/            # HA cluster
├── emailMarketing/              # Email marketing
├── emailPremium/                # Premium email
├── emailDelivery/               # Email delivery
├── webmail/                     # SnappyMail webmail
├── postfixSenderPolicy/         # SPF management
├── pluginHolder/                # Plugin registry
├── pluginInstaller/             # Plugin installer
├── examplePlugin/               # Plugin template
├── WebTerminal/                 # Web SSH terminal
├── CLManager/                   # CloudLinux integration
├── ApachController/             # Apache compatibility
├── baseTemplate/                # Base templates & version
├── api/                         # REST API
├── cli/                         # Command-line interface
├── static/                      # CSS, JS, images
├── install/                     # Installation scripts
├── scripts/                     # Utility scripts
├── tests/                       # Test suite (128 tests)
├── docs/                        # Documentation
├── guides/                      # User guides
├── locale/                      # i18n translations
├── lscpd-*                      # LiteSpeed binaries
├── install.sh                   # Installation entry point
├── cyberpanel.sh                # Main installation script
├── manage.py                    # Django management
├── requirments.txt              # Python dependencies
├── ubuntu-requirments.txt       # Ubuntu-specific dependencies
└── version.txt                  # Version info
```

---

## 13. Tích Hợp Đáng Chú Ý

| Dịch vụ | Mô tả |
|---|---|
| **OpenLiteSpeed** | Web server chính |
| **Postfix** | SMTP server |
| **OpenDKIM** | DKIM signing |
| **PowerDNS** | DNS server |
| **Let's Encrypt** | SSL certificates (ACME) |
| **SnappyMail** | Webmail client |
| **Mautic** | Email marketing platform |
| **CloudFlare** | DNS/CDN integration |
| **AWS S3** | Backup storage |
| **Google Drive** | Backup storage |
| **DigitalOcean Spaces** | Backup storage |
| **MINIO** | Self-hosted S3 storage |
| **Docker** | Container management |
| **CloudLinux** | CageFS + resource isolation |
| **phpMyAdmin** | Database admin interface |
| **WordPress** | CMS auto-installer + staging |

---

## 14. CI/CD & DevOps

### Version Control
- **Git branching:** `stable`, `vX.X.X`, `vX.X.X-dev`
- **Default branch:** Latest `vX.X.X-dev`
- Auto-delete old dev branches after merge

### Build Artifacts
- LiteSpeed binaries: `lscpd-0.2.7`, `lscpd-0.3.1`, `lscpd.0.4.0`, `lscpd.aarch64`
- Docker: `dockerManager/Dockerfile`, `docker-compose.yml`, `build.sh`, `entrypoint.sh`

### Systemd Services
- `fastapi_ssh_server.service` — FastAPI WebSocket SSH server
- `WebTerminal/cpssh.service` — Web terminal SSH service

### Logging
- Tập trung qua `CyberCPLogFileWriter`
- Multi-level: DEBUG, INFO, WARNING, ERROR
- Log files: `/var/log/cyberpanel/`

### Migration Tools
- `cPanelImporter.py` — Migrate từ cPanel sang CyberPanel
- `run_migration.py` — Database migration runner
