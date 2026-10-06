// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/PendingProjectService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.dto.PendingProjectDTO;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.ProjectNeighbor;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.ProjectNeighborRepository;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * fix181 (Section 8, 12.1 to 12.3): PENDING PROJECTS.
 *
 * An Employee enters a project in the field with NO money (no price, no payment). It is saved as Pending: hidden from
 * every money figure, Recovery and the nightly jobs (LandProjectRepository.findAll), shown in the Ledger's Pending tab.
 * The Employee may change it while it is Pending, add documents and notes, and see their own entries (MY ENTRIES).
 * A Secretary (or above) then fills in the prices and STARTS it (graduatePending) -- or REJECTS it with a reason.
 *
 * Every Employee path checks: the caller is an Employee, they entered the project, it is still Pending, not deleted.
 * The project row is locked first, so an Employee saving while a Secretary starts the same project cannot clash.
 * PRICING_FIELDS is THE list of money fields: refused from an Employee, the only ones graduatePending adds.
 */
@Service
@RequiredArgsConstructor
public class PendingProjectService {

    /** fix181 (8.6, 12.2): every money field of the intake form. */
    public static final List<String> PRICING_FIELDS = List.of(
            "totalCost", "initialPayment", "isStartAsReceivable", "monthlyStorageFee", "initialStorageFee",
            "initialStorageFeePaid", "lastPaidDate", "receivablesSince", "initialPaymentPayerNin",
            "initialStorageFeePaidPayerNin", "weeklyInstallment", "planType", "status costs");

    /** fix181 (17.8): a Pending project older than this many days is reminded once a day. */
    public static final int STALE_DAYS = 3;
    /** fix181 (12.3): how long MY ENTRIES shows a rejected or started entry. */
    public static final int RESULT_DAYS = 30;

    private final LandService landService;
    private final ProjectNumbersService projectNumbers;   // fix196
    private final com.gesolutions.erp.modules.client.service.ClientService clientService;   // fix194
    private final LandProjectRepository projectRepository;
    private final ProjectNeighborRepository neighborRepository;
    private final UserRepository userRepository;
    private final AuditService auditService;
    private final NotificationService notificationService;

    // ── who is calling ──────────────────────────────────────────────────────

    private User me() {
        String name = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByUsername(name)
                .orElseThrow(() -> new BusinessException("SECURITY_FAULT: Your session is not valid. Sign in again."));
    }

    /** The money fields this request carries (empty = none). */
    public static List<String> pricingFieldsSent(LandEntryRequest r) {
        List<String> sent = new ArrayList<>();
        if (positive(r.getTotalCost())) sent.add("totalCost");
        if (positive(r.getInitialPayment())) sent.add("initialPayment");
        if (r.isStartAsReceivable()) sent.add("isStartAsReceivable");
        if (positive(r.getMonthlyStorageFee())) sent.add("monthlyStorageFee");
        if (positive(r.getInitialStorageFee())) sent.add("initialStorageFee");
        if (positive(r.getInitialStorageFeePaid())) sent.add("initialStorageFeePaid");
        if (r.getLastPaidDate() != null) sent.add("lastPaidDate");
        if (r.getReceivablesSince() != null) sent.add("receivablesSince");
        if (notBlank(r.getInitialPaymentPayerNin())) sent.add("initialPaymentPayerNin");
        if (notBlank(r.getInitialStorageFeePaidPayerNin())) sent.add("initialStorageFeePaidPayerNin");
        if (positive(r.getWeeklyInstallment())) sent.add("weeklyInstallment");
        if (notBlank(r.getPlanType())) sent.add("planType");
        if (r.getSelectedStatuses() != null && r.getSelectedStatuses().stream().anyMatch(s -> positive(s.getCost()))) sent.add("status costs");
        return sent;
    }

    private static boolean positive(BigDecimal v) { return v != null && v.signum() != 0; }
    private static boolean notBlank(String v) { return v != null && !v.isBlank(); }

    private static void refuseMoney(LandEntryRequest r) {
        List<String> sent = pricingFieldsSent(r);
        if (!sent.isEmpty()) {
            throw new BusinessException("PRICING_NOT_ALLOWED: Prices and payments are added by the office, not on a field entry. Remove: " + String.join(", ", sent) + ".");
        }
    }

    /** The project, locked, entered by me, still Pending and not deleted. */
    private LandProject ownPending(UUID id, User me) {
        LandProject p = projectRepository.findByIdForUpdate(id)
                .orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        if (p.getCreatedById() == null || !p.getCreatedById().equals(me.getId())) {
            throw new BusinessException("NOT_YOUR_ENTRY: You can only open the projects you entered.");
        }
        if (p.isDeleted()) throw new BusinessException("ENTRY_REJECTED: This entry was rejected by the office" + (p.getDeletedReason() != null ? ": " + p.getDeletedReason() : "."));
        if (!p.isPending()) throw new BusinessException("ALREADY_STARTED: This project was already started by the office. Ask a Secretary.");
        return p;
    }

    private LandProject pendingForOffice(UUID id) {
        LandProject p = projectRepository.findByIdForUpdate(id)
                .orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        if (p.isDeleted()) throw new BusinessException("PROJECT_DELETED: This project is deleted.");
        if (!p.isPending()) throw new BusinessException("NOT_PENDING: This project is not Pending (it was already started).");
        return p;
    }

    // ── Employee ────────────────────────────────────────────────────────────

    @Transactional(rollbackFor = Exception.class)
    public PendingProjectDTO createPending(LandEntryRequest request, MultipartFile[] scans, List<String> categories) throws Exception {
        User me = me();
        refuseMoney(request);
        // an Employee never adds a custom status (canAddStatus is Manager and above)
        if (request.getSelectedStatuses() != null) request.getSelectedStatuses().removeIf(s -> s.isCustom());
        request.setInvoiceNumber(null); request.setContractNumber(null);   // fix196: the office adds the numbers, never a field entry
        LandProject saved = landService.doIntake(request, scans, categories, true);
        saved.setCreatedById(me.getId());
        saved.setCreatedBy(me.getUsername());
        projectRepository.save(saved);
        return toDto(saved, true);
    }

    @Transactional(rollbackFor = Exception.class)
    public PendingProjectDTO updateOwn(UUID id, LandEntryRequest request) {
        User me = me();
        LandProject p = ownPending(id, me);
        refuseMoney(request);
        request.setTotalCost(p.getTotalCost());           // nothing about the price can change here
        request.setCostChangeReason(null);
        request.setExpectedTotalCost(null);
        LandProject saved = landService.doUpdateProjectFull(id, request);
        // fix181 (13.6c): who changed a Pending project (sections only, never a price)
        auditService.logActionAfterCommit("PENDING_UPDATED", "Operator [" + me.getUsername() + "] edited Pending project #"
                + saved.getProjectIndex() + " (people, title details, location).");
        return toDto(saved, true);
    }

    @Transactional(rollbackFor = Exception.class)
    public void addDocuments(UUID id, MultipartFile[] scans, List<String> categories) throws Exception {
        ownPending(id, me());
        landService.requireScanFiles(scans);
        landService.addScansToProject(id, scans, null, categories);
    }

    @Transactional
    public void addNote(UUID id, String content) {
        ownPending(id, me());
        if (content == null || content.isBlank()) throw new BusinessException("NOTE_EMPTY: Write the note first.");
        landService.logNewNote(id, content.trim());
    }

    @Transactional(readOnly = true)
    public PendingProjectDTO viewOwn(UUID id) {
        User me = me();
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("PROJECT_NOT_FOUND: No such project."));
        if (me.getRole() == Role.ROLE_EMPLOYEE && (p.getCreatedById() == null || !p.getCreatedById().equals(me.getId()))) {
            throw new BusinessException("NOT_YOUR_ENTRY: You can only open the projects you entered.");
        }
        if (me.getRole() == Role.ROLE_EMPLOYEE && !p.isPending()) {
            throw new BusinessException("ALREADY_STARTED: This project was started by the office; it is no longer in your entries.");
        }
        return toDto(p, true);
    }

    /** MY ENTRIES: my Pending projects, plus the ones started or rejected in the last 30 days (with the reason). */
    @Transactional(readOnly = true)
    public List<PendingProjectDTO> mine() {
        User me = me();
        LocalDateTime since = LocalDateTime.now().minusDays(RESULT_DAYS);
        List<PendingProjectDTO> out = new ArrayList<>();
        for (LandProject p : projectRepository.findByCreatedById(me.getId())) {
            boolean show = (p.isPending() && !p.isDeleted())
                    || (p.isDeleted() && p.isPending() && p.getDeletedAt() != null && p.getDeletedAt().isAfter(since))
                    || (!p.isPending() && p.getGraduatedAt() != null && p.getGraduatedAt().isAfter(since));
            if (show) out.add(toDto(p, false));
        }
        return out;
    }

    // ── office (Secretary and above) ────────────────────────────────────────

    /**
     * fix181 (12.2): START a Pending project. The prices and the intake money go through the SAME checks as New Project
     * (LandService.checkIntakeMoney / applyIntakeMoney / recordIntakeMoney). People, title details and location may be
     * corrected in the same call (11.1b); the project type and subdivisions may not. No COST_CHANGED line is written.
     */
    @Transactional(rollbackFor = Exception.class)
    public LandProject graduatePending(UUID id, LandEntryRequest request) {
        LandProject p = pendingForOffice(id);
        if (request.getProjectType() != null && !request.getProjectType().isBlank()
                && p.getProjectType() != null && !request.getProjectType().equals(p.getProjectType())) {
            throw new BusinessException("PENDING_EDIT_DENIED: The project type cannot be changed while starting a project.");
        }
        LandService.IntakeMoney money = landService.checkIntakeMoney(request);
        if (money.totalCost().signum() <= 0) {
            throw new BusinessException("PRICE_REQUIRED: Enter the total cost (more than 0) before starting the project.");
        }
        // fix196: ONE step leaves Pending -- it needs the invoice number, the contract number AND the prices together
        String[] numbers = projectNumbers.check(p.getId(), request.getInvoiceNumber(), request.getContractNumber());
        // people / title / location corrections first, with the price held at 0 so no cost-change rules fire
        if (request.getDistrict() != null && !request.getDistrict().isBlank()) {
            LandEntryRequest people = copyWithoutMoney(request, p);
            landService.doUpdateProjectFull(id, people);
            p = projectRepository.findById(id).orElseThrow();
        }
        landService.applyIntakeMoney(p, money);
        p.setInvoiceNumber(numbers[0]);
        p.setContractNumber(numbers[1]);
        p.setPending(false);
        p.setGraduatedAt(LocalDateTime.now());
        LandProject saved = projectRepository.save(p);
        Map<String, Client> byNin = new LinkedHashMap<>();
        for (Client c : saved.billingParties()) if (c.getNationalId() != null) byNin.put(c.getNationalId().trim().toUpperCase(), c);
        String moneyNote = landService.recordIntakeMoney(saved, money, byNin, request);
        projectNumbers.tickStage(saved.getId());   // fix196: the Invoice / Contract stage is done
        auditService.logActionAfterCommit("PROJECT_GRADUATED", "Operator [" + AuditService.currentOperator() + "] priced and started Pending project #"
                + saved.getProjectIndex() + " (entered by " + saved.getCreatedBy() + "). Invoice " + saved.getInvoiceNumber() + ", contract " + saved.getContractNumber()
                + ". Total cost UGX " + money.totalCost().toPlainString() + moneyNote);
        notificationService.emitToAudience("PROJECT_GRADUATED", "Project " + saved.getProjectIndex() + " has been priced and started.",
                "PROJECT", saved.getId());
        return saved;
    }

    /** fix181 (12.3): reject a mistaken Pending entry (soft delete with a reason; the Employee sees the reason). */
    @Transactional
    public void rejectPending(UUID id, String reason) {
        String why = reason == null ? "" : reason.trim();
        if (why.length() < 5) throw new BusinessException("REASON_REQUIRED: Write why this entry is rejected (at least 5 characters).");
        LandProject p = pendingForOffice(id);
        p.setDeleted(true);
        p.setDeletedAt(LocalDateTime.now());
        p.setDeletedReason(why);
        p.setDeletedBy(AuditService.currentOperator());
        projectRepository.save(p);
        auditService.logActionAfterCommit("PROJECT_PENDING_REJECTED", "Operator [" + AuditService.currentOperator() + "] rejected Pending project #"
                + p.getProjectIndex() + " (entered by " + p.getCreatedBy() + "). Reason: " + why);
    }

    @Transactional(readOnly = true)
    public long countPending() {
        return projectRepository.countPending();
    }

    /** The people/title/location part of a graduation request, with every money field taken out. */
    private static LandEntryRequest copyWithoutMoney(LandEntryRequest r, LandProject p) {
        LandEntryRequest c = new LandEntryRequest();
        c.setTitleDetailsEnabled(r.isTitleDetailsEnabled());
        c.setSubdivisionCount(p.getSubdivisionCount());
        c.setPlotNumber(r.getPlotNumber()); c.setTenure(r.getTenure()); c.setBlock(r.getBlock());
        c.setAreaHectares(r.getAreaHectares()); c.setVolume(r.getVolume()); c.setFolio(r.getFolio());
        c.setDistrict(r.getDistrict()); c.setCounty(r.getCounty()); c.setSubCounty(r.getSubCounty());
        c.setParish(r.getParish()); c.setVillage(r.getVillage()); c.setArea(r.getArea());
        c.setProjectStartDate(r.getProjectStartDate()); c.setTitleIssueDate(r.getTitleIssueDate());
        c.setClients(r.getClients()); c.setOwners(r.getOwners()); c.setNeighbors(r.getNeighbors());
        c.setTotalCost(p.getTotalCost());
        return c;
    }

    // ── the small answer (8.8): never a price, a payment or a balance ───────

    PendingProjectDTO toDto(LandProject p, boolean withPeople) {
        var t = p.getLandTitle();
        PendingProjectDTO.PendingProjectDTOBuilder b = PendingProjectDTO.builder()
                .id(p.getId()).projectIndex(p.getProjectIndex()).projectType(p.getProjectType())
                .pending(p.isPending()).rejected(p.isDeleted()).rejectedReason(p.isDeleted() ? p.getDeletedReason() : null)
                .startedAt(p.getGraduatedAt()).enteredAt(p.getCreatedAt()).enteredBy(p.getCreatedBy())
                .ageDays(p.getCreatedAt() == null ? null : ChronoUnit.DAYS.between(p.getCreatedAt(), LocalDateTime.now()))
                .district(p.getDistrict()).county(p.getCounty()).subCounty(p.getSubCounty()).parish(p.getParish())
                .village(p.getVillage()).area(p.getArea()).projectStartDate(p.getProjectStartDate())
                .titleDetailsEnabled(p.isTitleDetailsEnabled()).subdivisionCount(p.getSubdivisionCount());
        if (t != null) {
            b.plotNumber(t.getPlotNumber()).block(t.getBlock()).tenure(t.getTenure()).areaHectares(t.getAreaHectares())
             .volume(t.getVolume()).folio(t.getFolio()).titleIssueDate(t.getTitleIssueDate());
        }
        if (withPeople) {
            b.clients(people(p.getClients())).owners(people(p.getProprietors()));
            List<PendingProjectDTO.Neighbor> ns = new ArrayList<>();
            for (ProjectNeighbor n : neighborRepository.findByProjectIdOrderByDisplayOrderAsc(p.getId())) {
                ns.add(new PendingProjectDTO.Neighbor(n.getFullName(), n.getPhone(), n.getSide(), n.getPlotNumber(), n.getNotes()));
            }
            b.neighbors(ns);
        } else {
            b.clientNames(p.getClients() == null ? List.of() : p.getClients().stream().map(Client::getFullName).sorted().toList());
        }
        return b.build();
    }

    // fix194 (review S01): an Employee gets the name and National ID they typed, but never the phone, email or address
    // of a client the office already has (ClientService.contactsLockedForCaller)
    private List<PendingProjectDTO.Person> people(Set<Client> cs) {
        if (cs == null) return List.of();
        return cs.stream().map(c -> {
            boolean hide = clientService.contactsLockedForCaller(c);
            return new PendingProjectDTO.Person(c.getId(), c.getFullName(), hide ? null : c.getPhoneNumber(),
                c.getNationalId(), hide ? null : c.getEmail(), hide ? null : c.getHomeAddress());
        }).sorted(Comparator.comparing(PendingProjectDTO.Person::fullName)).toList();
    }
}
