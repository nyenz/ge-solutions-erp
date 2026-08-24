package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.config.ApplicationConfig;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.FollowUpRepository;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.LandTitleRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=update",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "ge.solutions.jwt.secret=YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    "cloudinary.cloud-name=test",
    "cloudinary.api-key=test",
    "cloudinary.api-secret=test",
    "ADMIN_EMAIL=test@gesolutions.com",
    "ADMIN_DEFAULT_PASSWORD=TestPassword123",
    "MAIL_USERNAME=test@gmail.com",
    "MAIL_PASSWORD=testpassword"
})
public class LandCascadeDeleteTest {

    @Autowired
    private LandService landService;

    @Autowired
    private LandProjectRepository landProjectRepository;

    @Autowired
    private LandTitleRepository landTitleRepository;

    @Autowired
    private FollowUpRepository followUpRepository;

    @Autowired
    private PaymentRecordRepository paymentRecordRepository;

    @AfterEach
    public void clearSecurityContext() {
        SecurityContextHolder.clearContext();
    }

    private void mockRootAuthentication() {
        User mockUser = User.builder()
                .id(UUID.randomUUID())
                .username("admin_root")
                .email("root@test.com")
                .password("ignored")
                .role(Role.ROLE_ADMIN)
                .isRoot(true)
                .isActive(true)
                .mustChangePassword(false)
                .build();

        ApplicationConfig.CustomUserPrincipal principal = new ApplicationConfig.CustomUserPrincipal(mockUser);

        UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                principal,
                null,
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_ADMIN"))
        );
        SecurityContextHolder.getContext().setAuthentication(auth);
    }

    @Test
    public void testNuclearDeleteCascadesCorrectly() throws Exception {
        mockRootAuthentication();

        LandEntryRequest.OwnerRequest owner = LandEntryRequest.OwnerRequest.builder()
                .fullName("Cascade Test Owner")
                .phone("0711000999")
                .email("cascade@test.com")
                .nationalId("CM99999999ZZZZZ")
                .address("Kampala, Uganda")
                .build();

        List<LandEntryRequest.OwnerRequest> owners = new ArrayList<>();
        owners.add(owner);

        LandEntryRequest request = LandEntryRequest.builder()
                .plotNumber("CASCADE-001-TEST")
                .tenure("FREEHOLD")
                .blockRoad("Cascade Block")
                .district("Kampala")
                .county("Central")
                .volume("V99")
                .folio("F99")
                .instrumentNo("INS-CASCADE-001")
                .owners(owners)
                .totalCost(new BigDecimal("5000000"))
                .initialPayment(new BigDecimal("1000000"))
                .isLegacy(false)
                .isStartAsReceivable(false)
                .build();

        LandProject project = landService.atomicIntake(request, null);
        UUID projectId = project.getId();
        UUID titleId = project.getLandTitle().getId();

        landService.logNewNote(projectId, "Test cascade note - should be deleted");

        assertTrue(landProjectRepository.findById(projectId).isPresent(), "Project should exist before delete");
        assertTrue(landTitleRepository.findById(titleId).isPresent(), "Title should exist before delete");
        assertFalse(paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Payments should exist before delete");
        assertFalse(followUpRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Notes should exist before delete");

        landService.nuclearDelete(projectId);

        assertFalse(landProjectRepository.findById(projectId).isPresent(), "Project should be deleted");
        assertFalse(landTitleRepository.findById(titleId).isPresent(), "Title should be cascade-deleted");
        assertTrue(paymentRecordRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Payments should be deleted");
        assertTrue(followUpRepository.findByProjectIdOrderByTimestampDesc(projectId).isEmpty(), "Notes should be deleted");
    }
}
