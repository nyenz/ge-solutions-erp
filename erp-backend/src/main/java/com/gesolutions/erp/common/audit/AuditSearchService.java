// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditSearchService.java
package com.gesolutions.erp.common.audit;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.criteria.CriteriaBuilder;
import jakarta.persistence.criteria.CriteriaQuery;
import jakarta.persistence.criteria.Predicate;
import jakarta.persistence.criteria.Root;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;

/**
 * fix181 (10.13, 13.0e): THE audit search. Built as a criteria query so a LIST of action codes works (the old
 * `cast(:x as text) IS NULL` trick breaks on a list), and read-only on purpose: a Specification executor on the
 * repository would also add a delete method to a table that must stay append-only.
 *  - operator: exact name; actions: any of these codes (capped at 60); start inclusive, end EXCLUSIVE (the page sends
 *    the start of the day after "to", so the last second of the day is not lost, 10.11);
 *  - keyword: at most 100 characters, % and _ are plain letters, case-insensitive match in the details text;
 *  - newest first, then by id, so two rows with the same time never repeat or go missing between pages (10.5).
 */
@Service
public class AuditSearchService {

    public static final int MAX_ACTIONS = 60;
    public static final int MAX_KEYWORD = 100;

    @PersistenceContext
    private EntityManager em;

    public record Filter(String operator, Collection<String> actions, LocalDateTime start, LocalDateTime end,
                         String keyword, boolean excludeSystem) {}

    static String likePattern(String keyword) {
        String k = keyword.length() > MAX_KEYWORD ? keyword.substring(0, MAX_KEYWORD) : keyword;
        k = k.toLowerCase(Locale.ROOT).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");
        return "%" + k + "%";
    }

    private List<Predicate> where(CriteriaBuilder cb, Root<AuditLog> a, Filter f) {
        List<Predicate> p = new ArrayList<>();
        if (f.operator() != null && !f.operator().isBlank()) p.add(cb.equal(a.get("performedBy"), f.operator().trim()));
        if (f.actions() != null && !f.actions().isEmpty()) {
            List<String> codes = f.actions().stream().filter(c -> c != null && !c.isBlank()).map(String::trim)
                    .distinct().limit(MAX_ACTIONS).toList();
            if (!codes.isEmpty()) p.add(a.get("action").in(codes));
        }
        if (f.start() != null) p.add(cb.greaterThanOrEqualTo(a.get("timestamp"), f.start()));
        if (f.end() != null) p.add(cb.lessThan(a.get("timestamp"), f.end()));
        if (f.keyword() != null && !f.keyword().isBlank()) {
            p.add(cb.like(cb.lower(a.get("details")), likePattern(f.keyword().trim()), '\\'));
        }
        if (f.excludeSystem()) p.add(cb.notEqual(a.get("performedBy"), "SYSTEM"));
        return p;
    }

    @Transactional(readOnly = true)
    public Page<AuditLog> search(Filter f, int page, int size) {
        int s = Math.min(Math.max(size, 1), 200);
        int pg = Math.max(page, 0);
        CriteriaBuilder cb = em.getCriteriaBuilder();

        CriteriaQuery<AuditLog> q = cb.createQuery(AuditLog.class);
        Root<AuditLog> a = q.from(AuditLog.class);
        q.select(a).where(where(cb, a, f).toArray(new Predicate[0]))
                .orderBy(cb.desc(a.get("timestamp")), cb.asc(a.get("id")));
        List<AuditLog> rows = em.createQuery(q).setFirstResult(pg * s).setMaxResults(s).getResultList();

        CriteriaQuery<Long> cq = cb.createQuery(Long.class);
        Root<AuditLog> c = cq.from(AuditLog.class);
        cq.select(cb.count(c)).where(where(cb, c, f).toArray(new Predicate[0]));
        long total = em.createQuery(cq).getSingleResult();
        return new PageImpl<>(rows, PageRequest.of(pg, s), total);
    }

    /** Every name that appears in the audit trail (SYSTEM and people who were renamed or removed included), A to Z. */
    @Transactional(readOnly = true)
    public List<String> operators() {
        return em.createQuery("SELECT DISTINCT a.performedBy FROM AuditLog a WHERE a.performedBy IS NOT NULL ORDER BY a.performedBy", String.class)
                .getResultList();
    }
}
