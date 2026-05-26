import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

print("=== FIXING SYNTAX ERRORS ===")

# Fix PaymentsPage.jsx
path1 = 'erp-frontend/src/pages/Payments/PaymentsPage.jsx'
data1 = read(path1)
old1 = """                </HardwarePanel>
            )}
        </div>
    );
};"""
new1 = """                </HardwarePanel>
                </div>
            )}
        </div>
    );
};"""
if old1 in data1:
    data1 = data1.replace(old1, new1)
    write(path1, data1)
    print("OK: PaymentsPage.jsx syntax fixed")
else:
    print("MISSING: PaymentsPage.jsx")

# Fix LedgerPage.jsx
path2 = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'
data2 = read(path2)
old2 = """                </footer>
            </HardwarePanel>
        </div>
    );
};"""
new2 = """                </footer>
            </HardwarePanel>
            </div>
        </div>
    );
};"""
if old2 in data2:
    data2 = data2.replace(old2, new2)
    write(path2, data2)
    print("OK: LedgerPage.jsx syntax fixed")
else:
    print("MISSING: LedgerPage.jsx")

print("=== DONE ===")