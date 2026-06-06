"""
数据库初始化与表结构定义
"""
from core.database import get_cursor


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    budget_limit REAL NOT NULL DEFAULT 0,
    budget_used REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS procurement_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    estimated_amount REAL NOT NULL,
    required_date TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    attachments TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    budget_approved INTEGER DEFAULT 0,
    rejection_reason TEXT,
    submitted_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS tender_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER UNIQUE,
    project_code TEXT NOT NULL UNIQUE,
    project_name TEXT NOT NULL,
    category TEXT NOT NULL,
    budget_amount REAL NOT NULL,
    publish_date TEXT,
    bid_deadline TEXT,
    open_bid_date TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    template_id INTEGER,
    published_to_website INTEGER DEFAULT 0,
    published_to_portal INTEGER DEFAULT 0,
    weight_technical REAL NOT NULL DEFAULT 0.40,
    weight_commercial REAL NOT NULL DEFAULT 0.35,
    weight_qualification REAL NOT NULL DEFAULT 0.25,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id)
);

CREATE TABLE IF NOT EXISTS bid_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    category TEXT NOT NULL,
    min_amount REAL,
    max_amount REAL,
    content TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    unified_social_code TEXT UNIQUE,
    legal_representative TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    address TEXT,
    business_scope TEXT,
    qualification_level TEXT,
    credit_score REAL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    bid_amount REAL NOT NULL,
    delivery_date TEXT,
    encrypted_content TEXT,
    decrypted_content TEXT,
    decrypted_at TEXT,
    qualification_score REAL,
    technical_score REAL,
    commercial_score REAL,
    final_score REAL,
    ranking INTEGER,
    status TEXT NOT NULL DEFAULT 'submitted',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES tender_projects(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    UNIQUE(project_id, supplier_id)
);

CREATE TABLE IF NOT EXISTS experts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    expert_code TEXT NOT NULL UNIQUE,
    gender TEXT,
    title TEXT,
    organization TEXT,
    phone TEXT,
    email TEXT,
    specialty TEXT NOT NULL,
    sub_specialty TEXT,
    years_of_experience INTEGER,
    is_active INTEGER DEFAULT 1,
    avoid_suppliers TEXT,
    avoid_companies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expert_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    expert_id INTEGER NOT NULL,
    assignment_date TEXT,
    status TEXT NOT NULL DEFAULT 'assigned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES tender_projects(id),
    FOREIGN KEY (expert_id) REFERENCES experts(id),
    UNIQUE(project_id, expert_id)
);

CREATE TABLE IF NOT EXISTS expert_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    bid_id INTEGER NOT NULL,
    qualification_score REAL,
    technical_score REAL,
    commercial_score REAL,
    comment TEXT,
    scored_at TEXT,
    FOREIGN KEY (assignment_id) REFERENCES expert_assignments(id),
    FOREIGN KEY (bid_id) REFERENCES bids(id),
    UNIQUE(assignment_id, bid_id)
);

CREATE TABLE IF NOT EXISTS review_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE,
    report_content TEXT,
    generated_at TEXT,
    created_by TEXT,
    FOREIGN KEY (project_id) REFERENCES tender_projects(id)
);

CREATE TABLE IF NOT EXISTS awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE,
    winning_bid_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    award_amount REAL NOT NULL,
    award_date TEXT,
    notification_sent INTEGER DEFAULT 0,
    contract_generated INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    FOREIGN KEY (project_id) REFERENCES tender_projects(id),
    FOREIGN KEY (winning_bid_id) REFERENCES bids(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    award_id INTEGER NOT NULL UNIQUE,
    project_id INTEGER NOT NULL,
    contract_code TEXT NOT NULL UNIQUE,
    contract_content TEXT,
    signed_date TEXT,
    start_date TEXT,
    end_date TEXT,
    total_amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (award_id) REFERENCES awards(id),
    FOREIGN KEY (project_id) REFERENCES tender_projects(id)
);

CREATE TABLE IF NOT EXISTS performance_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    milestone_name TEXT NOT NULL,
    planned_date TEXT NOT NULL,
    actual_date TEXT,
    milestone_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    warning_sent INTEGER DEFAULT 0,
    comment TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    recipient_type TEXT NOT NULL,
    recipient_id INTEGER,
    recipient_email TEXT,
    project_id INTEGER,
    subject TEXT NOT NULL,
    content TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    sent_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL,
    module TEXT NOT NULL,
    record_id INTEGER,
    operator TEXT NOT NULL,
    detail TEXT,
    ip_address TEXT,
    pushed_to_group INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weekly_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL,
    week_end TEXT NOT NULL,
    total_projects INTEGER DEFAULT 0,
    avg_duration_days REAL DEFAULT 0,
    failed_bid_rate REAL DEFAULT 0,
    saved_amount REAL DEFAULT 0,
    report_path TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_database():
    with get_cursor() as cursor:
        cursor.executescript(SCHEMA_SQL)
    print("数据库初始化完成")


def seed_demo_data():
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM departments")
        if cursor.fetchone()[0] == 0:
            departments = [
                ('信息技术部', 10000000, 2300000),
                ('行政后勤部', 5000000, 800000),
                ('市场运营部', 8000000, 1500000),
                ('人力资源部', 3000000, 500000),
                ('研发中心', 20000000, 5000000),
            ]
            cursor.executemany(
                "INSERT INTO departments (name, budget_limit, budget_used) VALUES (?, ?, ?)",
                departments
            )

        cursor.execute("SELECT COUNT(*) FROM bid_templates")
        if cursor.fetchone()[0] == 0:
            templates = [
                ('货物类标准招标文件', 'goods', 0, 500000, '【货物类小额】标准招标文件模板内容...'),
                ('货物类大额招标文件', 'goods', 500000, 5000000, '【货物类中额】详细招标文件模板内容...'),
                ('货物类重大招标文件', 'goods', 5000000, 999999999, '【货物类大额】重大项目招标文件模板...'),
                ('工程类标准招标文件', 'engineering', 0, 5000000, '【工程类】标准招标文件模板...'),
                ('工程类重大招标文件', 'engineering', 5000000, 999999999, '【工程类重大】详细招标文件模板...'),
                ('服务类标准招标文件', 'service', 0, 1000000, '【服务类】标准招标文件模板...'),
                ('服务类大额招标文件', 'service', 1000000, 999999999, '【服务类大额】详细招标文件模板...'),
            ]
            cursor.executemany(
                "INSERT INTO bid_templates (template_name, category, min_amount, max_amount, content) VALUES (?, ?, ?, ?, ?)",
                templates
            )

        cursor.execute("SELECT COUNT(*) FROM suppliers")
        if cursor.fetchone()[0] == 0:
            suppliers = [
                ('北京科技发展有限公司', '91110000MA01ABC123', '张三', '李四', '13800138001', 'lisi@techbj.com', '北京市海淀区中关村大街1号', '软件开发、系统集成', '一级', 95.5),
                ('上海信息技术有限公司', '91310000MA01DEF456', '王五', '赵六', '13800138002', 'zhaoliu@shinfo.com', '上海市浦东新区张江高科技园区', 'IT咨询、云服务', '一级', 92.0),
                ('深圳智能科技有限公司', '91440300MA01GHI789', '钱七', '孙八', '13800138003', 'sunba@szsmart.com', '深圳市南山区科技园', '智能硬件、物联网', '二级', 88.5),
                ('广州网络服务有限公司', '91440100MA01JKL012', '周九', '吴十', '13800138004', 'wushi@gznet.com', '广州市天河区珠江新城', '网络安全、运维服务', '一级', 90.0),
                ('杭州数据科技有限公司', '91330100MA01MNO345', '郑十一', '王十二', '13800138005', 'wang12@hzdata.com', '杭州市西湖区文三路', '大数据分析、AI应用', '二级', 87.5),
                ('成都工程建设有限公司', '91510100MA01PQR678', '冯十三', '陈十四', '13800138006', 'chen14@cdbuild.com', '成都市高新区天府大道', '建筑工程、装修装饰', '特级', 93.0),
                ('武汉办公设备有限公司', '91420100MA01STU901', '褚十五', '卫十六', '13800138007', 'wei16@whoffice.com', '武汉市洪山区珞瑜路', '办公设备、家具', '三级', 85.0),
                ('南京咨询服务有限公司', '91320100MA01VWX234', '蒋十七', '沈十八', '13800138008', 'shen18@njconsult.com', '南京市鼓楼区中山路', '管理咨询、培训服务', '二级', 89.0),
            ]
            cursor.executemany(
                "INSERT INTO suppliers (company_name, unified_social_code, legal_representative, contact_person, contact_phone, contact_email, address, business_scope, qualification_level, credit_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                suppliers
            )

        cursor.execute("SELECT COUNT(*) FROM experts")
        if cursor.fetchone()[0] == 0:
            experts = [
                ('专家A', 'EXP001', '男', '教授级高工', '清华大学', '13900139001', 'exp001@expert.com', '软件开发', 'Java架构', 20, '北京科技发展有限公司;上海信息技术有限公司', ''),
                ('专家B', 'EXP002', '女', '高级工程师', '中科院', '13900139002', 'exp002@expert.com', '软件开发', 'Python/AI', 15, '', '深圳智能科技有限公司'),
                ('专家C', 'EXP003', '男', '研究员', '北航', '13900139003', 'exp003@expert.com', '网络安全', '信息安全', 18, '广州网络服务有限公司', ''),
                ('专家D', 'EXP004', '女', '教授', '北大', '13900139004', 'exp004@expert.com', '大数据', '数据分析', 12, '', '杭州数据科技有限公司'),
                ('专家E', 'EXP005', '男', '高级工程师', '信通院', '13900139005', 'exp005@expert.com', '系统集成', '云计算', 22, '', ''),
                ('专家F', 'EXP006', '男', '教授级高工', '哈工大', '13900139006', 'exp006@expert.com', '软件开发', '数据库', 25, '北京科技发展有限公司', ''),
                ('专家G', 'EXP007', '女', '高级经济师', '财政部', '13900139007', 'exp007@expert.com', '商务评标', '价格分析', 20, '', ''),
                ('专家H', 'EXP008', '男', '高级工程师', '住建部', '13900139008', 'exp008@expert.com', '工程建设', '施工管理', 30, '成都工程建设有限公司', ''),
                ('专家I', 'EXP009', '女', '教授', '复旦', '13900139009', 'exp009@expert.com', '咨询服务', '管理咨询', 18, '', '南京咨询服务有限公司'),
                ('专家J', 'EXP010', '男', '高级工程师', '电子六所', '13900139010', 'exp010@expert.com', '智能硬件', '物联网', 16, '', ''),
            ]
            cursor.executemany(
                "INSERT INTO experts (name, expert_code, gender, title, organization, phone, email, specialty, sub_specialty, years_of_experience, avoid_suppliers, avoid_companies) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                experts
            )

    print("演示数据已加载")
