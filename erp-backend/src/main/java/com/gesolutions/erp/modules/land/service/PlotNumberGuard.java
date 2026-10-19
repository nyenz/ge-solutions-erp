package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.LandTitle;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.Locale;
import java.util.UUID;

/**
 * fix213 (David, test step N2): a plot number is only "taken" inside the same BLOCK and DISTRICT.
 * Plot 214 in Block 7, Iganga and plot 214 in Block 9, Kamuli are two different pieces of land.
 * The old rule (one plot number in the whole system, a database UNIQUE on land_titles.plot_number)
 * is dropped at start-up by DataInitializer. Comparison ignores capitals and extra spaces.
 */
@Component
@RequiredArgsConstructor
public class PlotNumberGuard {

    private final LandProjectRepository projectRepository;

    public void assertFree(String plot, String block, String district, UUID selfId) {
        if (plot == null || plot.isBlank()) return;
        String key = key(plot, block, district);
        for (LandProject other : projectRepository.findAllIncludingPending()) {
            if (selfId != null && selfId.equals(other.getId())) continue;
            LandTitle t = other.getLandTitle();
            if (t == null || t.getPlotNumber() == null) continue;
            if (key.equals(key(t.getPlotNumber(), t.getBlock(), other.getDistrict()))) {
                throw new BusinessException("PLOT_TAKEN: Plot number " + plot.trim()
                        + (block == null || block.isBlank() ? "" : ", Block " + block.trim())
                        + (district == null || district.isBlank() ? "" : " in " + district.trim())
                        + " is already on project #" + other.getProjectIndex() + ".");
            }
        }
    }

    static String key(String plot, String block, String district) {
        return n(plot) + "|" + n(block) + "|" + n(district);
    }

    private static String n(String v) {
        return v == null ? "" : v.trim().replaceAll("\\s+", " ").toLowerCase(Locale.ROOT);
    }
}
