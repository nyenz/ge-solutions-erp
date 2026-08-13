# PATH: fix.py
# PHASE 2 - NIN-BASED IDENTITY
# Run this from the project root: py fix.py
#
# WHAT THIS PATCH DOES (matches Section 17.3 of LLM_CONTEXT_GUIDE.md):
#   1. National ID (NIN) becomes MANDATORY for every owner at Intake and on Edit.
#   2. People are now matched/created by NIN instead of by phone number.
#      - Different NIN on a re-registration = treated as a brand new person.
#      - Existing NIN found = staff get an auto-fill (still editable) on blur.
#      - Existing NIN under a DIFFERENT name = staff get a typo warning (not blocked).
#   3. Phone number uniqueness is DOWNGRADED (removed as a hard DB constraint) since
#      joint owners / family members can now legitimately share a phone number --
#      NIN is the real uniqueness check going forward.
#   4. New endpoint: GET /api/v1/clients/lookup-nin?nin=XXXX for the frontend to
#      check a NIN before/while the form is being filled in.
#
# KNOWN LIMITATION (expected, not a bug): old client records created before this
# patch may have a blank national_id. That is fine -- they simply won't match
# anything via NIN lookup until they are next edited and given a real NIN.

import os

def read_file(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def write_file(path, content):
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  -> Saved: {path}")

def patch_file(path, anchor, replacement, label):
    content = read_file(path)
    if content is None:
        print(f"FAIL: {label} ({path} not found)")
        return
    if anchor not in content:
        print(f"MISSING: {label} (anchor not found in {path} -- may already be patched, or file changed)")
        return
    if content.count(anchor) > 1:
        print(f"WARN: {label} (anchor appears more than once in {path} -- patching first occurrence only)")
    content = content.replace(anchor, replacement, 1)
    write_file(path, content)
    print(f"OK: {label}")

print("Starting Phase 2 Patch - NIN-Based Identity...")
print("-" * 60)

# ============================================================
# BACKEND 1/8: DataInitializer.java -- schema migrations
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"
anchor = """            // PHASE 1.5 - DATE TRACKING SYSTEM
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",
        };"""
replacement = """            // PHASE 1.5 - DATE TRACKING SYSTEM
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",

            // PHASE 2 - NIN-BASED IDENTITY
            // Unique constraint on national_id. Postgres allows multiple NULLs under
            // a UNIQUE constraint, so old clients with no NIN yet are not affected.
            "ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id)",
            // Phone numbers are no longer required to be unique -- joint owners or
            // family members can share one phone. NIN is now the real identity check.
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",
        };"""
patch_file(path, anchor, replacement, "1/8 DataInitializer.java (Phase 2 migrations)")

# ============================================================
# BACKEND 2/8: Client.java -- full rewrite (drop unique=true on phone)
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/model/Client.java"
content = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/model/Client.java
package com.gesolutions.erp.modules.client.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.time.Month;
import java.util.UUID;

/**
 * GE SOLUTIONS - HUMAN IDENTITY REGISTRY
 *
 * PHASE 2: Identity is now anchored on National ID (NIN), not phone number.
 * Phone number is still required as a contact field, but is no longer
 * enforced as unique at the database level -- joint owners or family
 * members may legitimately share one phone.
 *
 * Physically manages the "Recovery Cool-Down" logic:
 * - 14-Day Interval Check
 * - 2-Call Per Month Handbrake
 */
@Entity
@Table(name = "clients", indexes = {
    @Index(name = "idx_client_phone", columnList = "phone_number"),
    @Index(name = "idx_client_nin", columnList = "national_id"),
    @Index(name = "idx_client_last_call", columnList = "last_contacted_at")
})
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class Client {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    // NOTE: unique=true intentionally removed in Phase 2 -- see DataInitializer
    // migration that drops the old DB-level unique constraint on this column.
    @Column(name = "phone_number", nullable = false, length = 50)
    private String phoneNumber;

    /**
     * NATIONAL ID (NIN) -- THE REAL IDENTITY ANCHOR (Phase 2)
     * Mandatory for every project owner going forward. Unique at the DB level
     * (see DataInitializer). Legacy client rows created before Phase 2 may
     * have this blank until next edited.
     */
    @Column(name = "national_id", length = 100)
    private String nationalId;

    @Column(name = "home_address", columnDefinition = "TEXT")
    private String homeAddress;

    @Column(name = "email")
    private String email;

    /* --- RECOVERY ARCHITECTURE (THE 2-14 RULE) --- */

    @Column(name = "last_contacted_at")
    private LocalDateTime lastContactedAt;

    /**
     * THE MONTHLY COUNTER
     * Physically counts successful interactions in the current month.
     */
    @Builder.Default
    @Column(name = "monthly_contact_count", nullable = false)
    private Integer monthlyContactCount = 0;

    /**
     * RELIABILITY METER (0-100)
     * Decreases on defaults, increases on successful calls and payments.
     */
    @Builder.Default
    @Column(name = "reliability_score", nullable = false)
    private Double reliabilityScore = 100.0;

    /**
     * HARDWARE LOGIC: Contact Suppression Check
     * This method tells the system if the counter needs to be reset 
     * before a new call is logged.
     */
    public boolean shouldResetMonthlyCounter() {
        if (lastContactedAt == null) return true;
        
        Month currentMonth = LocalDateTime.now().getMonth();
        int currentYear = LocalDateTime.now().getYear();
        
        return lastContactedAt.getMonth() != currentMonth || lastContactedAt.getYear() != currentYear;
    }
}
"""
write_file(path, content)
print("OK: 2/8 Client.java (unique=true removed from phone_number, national_id indexed)")

# ============================================================
# BACKEND 3/8: ClientRepository.java -- full rewrite (add findByNationalId)
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/repository/ClientRepository.java"
content = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/repository/ClientRepository.java
package com.gesolutions.erp.modules.client.repository;

import com.gesolutions.erp.modules.client.model.Client;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ClientRepository extends JpaRepository<Client, UUID> {

    Optional<Client> findByPhoneNumber(String phoneNumber);

    /**
     * PHASE 2: THE REAL IDENTITY LOOKUP
     * Used at intake and edit time to find an existing person by NIN,
     * and by the /clients/lookup-nin endpoint for pre-submit duplicate checks.
     */
    Optional<Client> findByNationalId(String nationalId);

    @Query(value = "SELECT * FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2 " +
                   "ORDER BY c.last_contacted_at ASC", nativeQuery = true)
    List<Client> findStaleClientsForRecovery();

    @Query(value = "SELECT COUNT(*) FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2", nativeQuery = true)
    long countTotalStaleClients();

    @Query(value = "SELECT COUNT(DISTINCT c.phone_number) FROM clients c " +
                   "WHERE (c.last_contacted_at IS NULL " +
                   "OR c.last_contacted_at <= CURRENT_TIMESTAMP - INTERVAL '14 days') " +
                   "AND c.monthly_contact_count < 2", nativeQuery = true)
    long countUniqueEligiblePhones();

    boolean existsByNationalId(String nationalId);
}
"""
write_file(path, content)
print("OK: 3/8 ClientRepository.java (added findByNationalId)")

# ============================================================
# BACKEND 4/8: ClientService.java -- add findOrCreateClientByNin
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/service/ClientService.java"
anchor = """    /**
     * SYSTEM UTILITY: ADJUST RELIABILITY
     * Manually adjusted by financial events (e.g., missed payments lower score).
     */
    @Transactional
    public void adjustReliability(UUID clientId, double delta) {"""
replacement = """    /**
     * PHASE 2: NIN-BASED IDENTITY LOOKUP
     * Finds an existing person by their National ID (NIN), or creates a new one.
     * Per business rule (Section 17.3): if a person's NIN changes, they are
     * treated as a brand new person record -- this method never merges by
     * name or phone, only ever by NIN.
     */
    @Transactional
    public Client findOrCreateClientByNin(String fullName, String nin, String phone, String email) {
        if (nin == null || nin.isBlank()) {
            throw new BusinessException("NIN_REQUIRED: A National ID (NIN) is mandatory for every project owner.");
        }
        String normalizedNin = nin.trim().toUpperCase();

        return clientRepository.findByNationalId(normalizedNin)
                .orElseGet(() -> {
                    Client newClient = Client.builder()
                            .fullName(fullName)
                            .phoneNumber(phone)
                            .nationalId(normalizedNin)
                            .email(email)
                            .monthlyContactCount(0)
                            .reliabilityScore(100.0)
                            .build();

                    Client saved = clientRepository.save(newClient);
                    auditService.logAction("CLIENT_ARCHIVE",
                        "New identity registered via NIN: " + fullName + " (" + normalizedNin + ")");
                    return saved;
                });
    }

    /**
     * SYSTEM UTILITY: ADJUST RELIABILITY
     * Manually adjusted by financial events (e.g., missed payments lower score).
     */
    @Transactional
    public void adjustReliability(UUID clientId, double delta) {"""
patch_file(path, anchor, replacement, "4/8 ClientService.java (findOrCreateClientByNin)")

# ============================================================
# BACKEND 5/8: LandService.java -- atomicIntake now requires + uses NIN
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"
anchor = """        if (request.getOwners() != null) {
            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {
                Client c = clientService.findOrCreateClient(o.getFullName(), o.getPhone(), o.getEmail());
                c.setNationalId(o.getNationalId());
                c.setHomeAddress(o.getAddress());
                project.addProprietor(c);
            }
        }"""
replacement = """        if (request.getOwners() != null) {
            for (LandEntryRequest.OwnerRequest o : request.getOwners()) {
                if (o.getNationalId() == null || o.getNationalId().isBlank()) {
                    throw new BusinessException("NIN_REQUIRED: Owner \\"" + o.getFullName() + "\\" is missing a National ID (NIN).");
                }
                Client c = clientService.findOrCreateClientByNin(o.getFullName(), o.getNationalId(), o.getPhone(), o.getEmail());
                c.setHomeAddress(o.getAddress());
                project.addProprietor(c);
            }
        }"""
patch_file(path, anchor, replacement, "5/8 LandService.java atomicIntake (NIN required)")

# ============================================================
# BACKEND 6/8: LandService.java -- updateProjectFull now matches by NIN
# ============================================================
anchor2 = """        if (request.getOwners() != null) {
            Set<Client> updatedRegistry = new HashSet<>();
            for (LandEntryRequest.OwnerRequest incoming : request.getOwners()) {
                Client person = clientRepository.findByPhoneNumber(incoming.getPhone())
                        .orElseGet(() -> clientService.findOrCreateClient(
                                incoming.getFullName(), incoming.getPhone(), incoming.getEmail()));
                person.setFullName(incoming.getFullName().toUpperCase());
                person.setNationalId(incoming.getNationalId() != null
                        ? incoming.getNationalId().toUpperCase() : null);
                person.setEmail(incoming.getEmail() != null
                        ? incoming.getEmail().toLowerCase() : null);
                person.setHomeAddress(incoming.getAddress());
                clientRepository.save(person);
                updatedRegistry.add(person);
            }
            project.setProprietors(updatedRegistry);
        }"""
replacement2 = """        if (request.getOwners() != null) {
            Set<Client> updatedRegistry = new HashSet<>();
            for (LandEntryRequest.OwnerRequest incoming : request.getOwners()) {
                if (incoming.getNationalId() == null || incoming.getNationalId().isBlank()) {
                    throw new BusinessException("NIN_REQUIRED: Owner \\"" + incoming.getFullName() + "\\" is missing a National ID (NIN).");
                }
                String normalizedNin = incoming.getNationalId().trim().toUpperCase();
                Client person = clientRepository.findByNationalId(normalizedNin)
                        .orElseGet(() -> clientService.findOrCreateClientByNin(
                                incoming.getFullName(), normalizedNin, incoming.getPhone(), incoming.getEmail()));
                person.setFullName(incoming.getFullName().toUpperCase());
                person.setNationalId(normalizedNin);
                person.setEmail(incoming.getEmail() != null
                        ? incoming.getEmail().toLowerCase() : null);
                person.setHomeAddress(incoming.getAddress());
                if (incoming.getPhone() != null && !incoming.getPhone().isBlank()) {
                    person.setPhoneNumber(incoming.getPhone());
                }
                clientRepository.save(person);
                updatedRegistry.add(person);
            }
            project.setProprietors(updatedRegistry);
        }"""
patch_file(path, anchor2, replacement2, "6/8 LandService.java updateProjectFull (NIN required)")

# ============================================================
# BACKEND 7/8: ClientController.java -- NEW FILE (NIN lookup endpoint)
# ============================================================
path = "erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java"
content = """// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java
package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * GE SOLUTIONS - PHASE 2 IDENTITY LOOKUP
 *
 * Lets the frontend check a National ID (NIN) before or while a form is
 * being filled in, so staff can be warned about a likely typo (NIN already
 * registered to a different name) or have known details auto-filled
 * (NIN matches an existing person), per Section 17.3.
 */
@RestController
@RequestMapping("/api/v1/clients")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN')")
public class ClientController {

    private final ClientRepository clientRepository;

    @GetMapping("/lookup-nin")
    public ResponseEntity<Map<String, Object>> lookupByNin(@RequestParam String nin) {
        Map<String, Object> result = new HashMap<>();

        if (nin == null || nin.isBlank()) {
            result.put("exists", false);
            return ResponseEntity.ok(result);
        }

        return clientRepository.findByNationalId(nin.trim().toUpperCase())
                .map(c -> {
                    result.put("exists", true);
                    result.put("fullName", c.getFullName());
                    result.put("phoneNumber", c.getPhoneNumber());
                    result.put("email", c.getEmail());
                    result.put("homeAddress", c.getHomeAddress());
                    result.put("nationalId", c.getNationalId());
                    return ResponseEntity.ok(result);
                })
                .orElseGet(() -> {
                    result.put("exists", false);
                    return ResponseEntity.ok(result);
                });
    }
}
"""
write_file(path, content)
print("OK: 7/8 ClientController.java (new file - GET /api/v1/clients/lookup-nin)")

# ============================================================
# FRONTEND 8/8a: clientService.js -- NEW FILE
# ============================================================
path = "erp-frontend/src/services/clientService.js"
content = """// PATH: erp-frontend/src/services/clientService.js
import api from '../api/axios';

const clientService = {
    // PHASE 2: check a NIN before/while the form is filled in.
    // Returns { exists: false } on any error so the UI never blocks on this.
    lookupNin: async (nin) => {
        if (!nin || !nin.trim()) return { exists: false };
        try {
            const response = await api.get('/clients/lookup-nin', {
                params: { nin: nin.trim().toUpperCase() }
            });
            return response.data;
        } catch {
            return { exists: false };
        }
    }
};

export default clientService;
"""
write_file(path, content)
print("OK: 8a/8 clientService.js (new file)")

# ============================================================
# FRONTEND 8b: IntakePage.jsx -- NIN required + duplicate check
# ============================================================
path = "erp-frontend/src/pages/Intake/IntakePage.jsx"

anchor = """import predictionService from '../../services/predictionService';
import styles from './IntakePage.module.css';"""
replacement = """import predictionService from '../../services/predictionService';
import clientService from '../../services/clientService';
import styles from './IntakePage.module.css';"""
patch_file(path, anchor, replacement, "8b-1/8 IntakePage.jsx (import clientService)")

anchor = """const SmartInput = ({ label, value, onChange, placeholder, suggestions = [], showCaps, required, error, inputMode, maxLength, hint, id }) => {
    const inputId = id || 'si-' + (label || '').replace(/\\W/g, '-').toLowerCase();
    return (
        <div className={`${styles.inputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
                {showCaps && <span className={styles.capsBadge}>CAPS</span>}
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                type="text" value={value} onChange={onChange} placeholder={placeholder}
                inputMode={inputMode} maxLength={maxLength} autoComplete="off"
                list={suggestions.length ? inputId + '_dl' : undefined} />"""
replacement = """const SmartInput = ({ label, value, onChange, onBlur, placeholder, suggestions = [], showCaps, required, error, inputMode, maxLength, hint, id }) => {
    const inputId = id || 'si-' + (label || '').replace(/\\W/g, '-').toLowerCase();
    return (
        <div className={`${styles.inputWrap} ${error ? styles.inputError : ''}`}>
            <div className={styles.labelRow}>
                <label htmlFor={inputId} className={styles.fieldLabel}>
                    {label}{required && <span className={styles.requiredStar}> *</span>}
                </label>
                {showCaps && <span className={styles.capsBadge}>CAPS</span>}
            </div>
            <input id={inputId} className={`${styles.hwInput} ${error ? styles.hwInputErr : ''}`}
                type="text" value={value} onChange={onChange} onBlur={onBlur} placeholder={placeholder}
                inputMode={inputMode} maxLength={maxLength} autoComplete="off"
                list={suggestions.length ? inputId + '_dl' : undefined} />"""
patch_file(path, anchor, replacement, "8b-2/8 IntakePage.jsx (SmartInput onBlur support)")

anchor = """        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
        });"""
replacement = """        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
            if (!o.nationalId.trim())  e['owner_' + i + '_nin']   = 'Required';
        });"""
patch_file(path, anchor, replacement, "8b-3/8 IntakePage.jsx (NIN required in validate())")

anchor = """    // Warn if a phone number is already used by another owner on this form
    const handlePhoneBlurCheck = (idx, val) => {"""
replacement = """    // PHASE 2: NIN duplicate/auto-fill check. Warns on likely typo (NIN already
    // registered under a different name), auto-fills known details on a real match.
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            toast(`WARNING: This NIN is already registered to "${result.fullName}". Check for a typo.`, 'warn', 6000);
            return;
        }

        setOwners(prev => prev.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                fullName: o.fullName.trim() ? o.fullName : (result.fullName || o.fullName),
                phone:    o.phone.trim()    ? o.phone    : (result.phoneNumber || o.phone),
                email:    o.email.trim()    ? o.email    : (result.email || o.email),
                address:  o.address.trim()  ? o.address  : (result.homeAddress || o.address),
            };
        }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };

    // Warn if a phone number is already used by another owner on this form
    const handlePhoneBlurCheck = (idx, val) => {"""
patch_file(path, anchor, replacement, "8b-4/8 IntakePage.jsx (handleNinBlurCheck)")

anchor = """                                        <SmartInput label="NATIONAL ID (NIN)" value={o.nationalId} showCaps
                                            maxLength={14}
                                            onChange={e => updateOwner(idx, 'nationalId', e.target.value.toUpperCase().replace(/\\s/g,''))} />"""
replacement = """                                        <SmartInput label="NATIONAL ID (NIN)" value={o.nationalId} showCaps required
                                            error={errors['owner_'+idx+'_nin']}
                                            maxLength={14}
                                            onChange={e => updateOwner(idx, 'nationalId', e.target.value.toUpperCase().replace(/\\s/g,''))}
                                            onBlur={e => handleNinBlurCheck(idx, e.target.value)} />"""
patch_file(path, anchor, replacement, "8b-5/8 IntakePage.jsx (NIN input wired to duplicate check)")

# ============================================================
# FRONTEND 8c: FolderPage.jsx -- same NIN required + duplicate check
# ============================================================
path = "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"

anchor = """import predictionService from '../../services/predictionService';
import HardwareModal from '../../components/common/HardwareModal';"""
replacement = """import predictionService from '../../services/predictionService';
import clientService from '../../services/clientService';
import HardwareModal from '../../components/common/HardwareModal';"""
patch_file(path, anchor, replacement, "8c-1/8 FolderPage.jsx (import clientService)")

anchor = """const NINInput = ({ label = 'NATIONAL ID / NIN', value, onChange, id }) => {
    const inputId = id || 'nin_input';
    const MAX = 14;
    const handleChange = (e) => onChange(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,MAX));
    return (
        <div className={styles.hwInputWrap}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}</label>
                <span className={styles.capsBadge}>CAPS</span>
            </div>
            <input id={inputId} type="text" value={value} onChange={handleChange}
                maxLength={MAX} placeholder="CM90XXXXXXXX12"
                className={styles.hwInput} autoComplete="off" autoCapitalize="characters" />
        </div>
    );
};"""
replacement = """const NINInput = ({ label = 'NATIONAL ID / NIN', value, onChange, onBlur, id, required }) => {
    const inputId = id || 'nin_input';
    const MAX = 14;
    const handleChange = (e) => onChange(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,MAX));
    return (
        <div className={styles.hwInputWrap}>
            <div className={styles.inputLabelRow}>
                <label htmlFor={inputId}>{label}{required && <span className={styles.reqStar}> *</span>}</label>
                <span className={styles.capsBadge}>CAPS</span>
            </div>
            <input id={inputId} type="text" value={value} onChange={handleChange} onBlur={onBlur}
                maxLength={MAX} placeholder="CM90XXXXXXXX12"
                className={styles.hwInput} autoComplete="off" autoCapitalize="characters" />
        </div>
    );
};"""
patch_file(path, anchor, replacement, "8c-2/8 FolderPage.jsx (NINInput onBlur + required support)")

anchor = """    buffer.owners?.forEach((o, i) => {
        if (!o.fullName?.trim()) errors.push(`OWNER ${i + 1}: LEGAL NAME IS REQUIRED`);
    });"""
replacement = """    buffer.owners?.forEach((o, i) => {
        if (!o.fullName?.trim()) errors.push(`OWNER ${i + 1}: LEGAL NAME IS REQUIRED`);
        if (!o.nationalId?.trim()) errors.push(`OWNER ${i + 1}: NATIONAL ID (NIN) IS REQUIRED`);
    });"""
patch_file(path, anchor, replacement, "8c-3/8 FolderPage.jsx (NIN required in validateBuffer)")

anchor = """    const handlePhoneBlurCheck = (idx, val) => {
        if (!val.trim()) return;
        const normalized = val.replace(/\\s+/g, '');
        const duplicate = (buffer.owners || []).some((o, i) =>
            i !== idx && o.phone.replace(/\\s+/g, '') === normalized
        );
        if (duplicate) {
            toast('WARNING: This phone number is already used by another owner on this plot.', 'warn', 5000);
        }
    };"""
replacement = """    // PHASE 2: NIN duplicate/auto-fill check on edit -- same behavior as Intake.
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (buffer.owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            toast(`WARNING: This NIN is already registered to "${result.fullName}". Check for a typo.`, 'warn', 6000);
            return;
        }

        const owners = buffer.owners.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                phone:   o.phone.trim()   ? o.phone   : (result.phoneNumber || o.phone),
                email:   o.email.trim()   ? o.email   : (result.email || o.email),
                address: o.address.trim() ? o.address : (result.homeAddress || o.address),
            };
        });
        touchedSetBuffer(p => ({ ...p, owners }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };

    const handlePhoneBlurCheck = (idx, val) => {
        if (!val.trim()) return;
        const normalized = val.replace(/\\s+/g, '');
        const duplicate = (buffer.owners || []).some((o, i) =>
            i !== idx && o.phone.replace(/\\s+/g, '') === normalized
        );
        if (duplicate) {
            toast('WARNING: This phone number is already used by another owner on this plot.', 'warn', 5000);
        }
    };"""
patch_file(path, anchor, replacement, "8c-4/8 FolderPage.jsx (handleNinBlurCheck)")

anchor = """                                            <NINInput value={o.nationalId} onChange={v => handleOwnerChange(idx,'nationalId',v)} id={`owner_${idx}_nin`} />"""
replacement = """                                            <NINInput value={o.nationalId} required
                                                onChange={v => handleOwnerChange(idx,'nationalId',v)}
                                                onBlur={e => handleNinBlurCheck(idx, e.target.value)}
                                                id={`owner_${idx}_nin`} />"""
patch_file(path, anchor, replacement, "8c-5/8 FolderPage.jsx (NIN input wired to duplicate check)")

print("-" * 60)
print("DONE. Check for FAIL / MISSING messages above.")
print("")
print("If everything shows OK, run:")
print("git add -A && git commit -m 'feat: Phase 2 - NIN-based identity' && git push")
print("")
print("IMPORTANT BEFORE YOU DEPLOY:")
print("  - NIN is now REQUIRED on every new plot intake and every edit.")
print("  - Existing plots you edit will now demand a NIN for each owner")
print("    before the save will go through -- have that ready.")
print("  - Phone numbers are no longer unique in the database. If the")
print("    'ALTER TABLE clients DROP CONSTRAINT' migration line fails on")
print("    Render startup because your DB never had that exact constraint")
print("    name, that is harmless -- it is wrapped in a try/catch and the")
print("    app will still start normally.")
print("")
print("TEST PLAN ONCE DEPLOYED:")
print("  1. Create a new plot, leave an owner's NIN blank -> should be blocked.")
print("  2. Create a new plot with a NIN you already used before -> should")
print("     auto-fill that owner's phone/email/address on blur.")
print("  3. Create a new plot with an existing NIN but type the name")
print("     slightly wrong -> should show an orange typo warning, not block.")
print("  4. Open an existing plot, edit mode, confirm NIN field shows the")
print("     required red asterisk and blocks save if cleared.")