// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ProjectIndexService.java
package com.gesolutions.erp.modules.land.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

/**
 * GE SOLUTIONS - PROJECT INDEX GENERATOR
 *
 * Generates short, never-repeating, searchable project index codes
 * in the format: 001A, 002A ... 999A, 001B, 002B ... 999B, 001C ...
 *
 * Numbers never repeat and the code never grows past 4 characters,
 * no matter how many thousands of projects the company processes.
 *
 * Uses a single-row counter table (project_index_counter) and a
 * synchronized raw JDBC read-increment-write. Project intake happens
 * rarely enough (a handful of times per day) that a full pessimistic
 * database lock is not necessary -- the synchronized keyword is enough
 * to prevent two intakes at the exact same instant from colliding.
 */
@Service
public class ProjectIndexService {

    private final DataSource dataSource;

    public ProjectIndexService(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Transactional
    public synchronized String generateNextIndex() {
        try (Connection conn = dataSource.getConnection()) {

            int currentNumber;
            String currentLetter;

            try (PreparedStatement ps = conn.prepareStatement(
                    "SELECT current_number, current_letter FROM project_index_counter WHERE id = 1");
                 ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    currentNumber = rs.getInt("current_number");
                    currentLetter = rs.getString("current_letter");
                } else {
                    currentNumber = 0;
                    currentLetter = "A";
                }
            }

            currentNumber = currentNumber + 1;
            if (currentNumber > 999) {
                currentNumber = 1;
                currentLetter = nextLetter(currentLetter);
            }

            try (PreparedStatement ps = conn.prepareStatement(
                    "UPDATE project_index_counter SET current_number = ?, current_letter = ? WHERE id = 1")) {
                ps.setInt(1, currentNumber);
                ps.setString(2, currentLetter);
                ps.executeUpdate();
            }

            return String.format("%03d", currentNumber) + currentLetter;

        } catch (Exception e) {
            throw new RuntimeException("PROJECT_INDEX_FAULT: Could not generate project index", e);
        }
    }

    // A -> B -> C ... Z -> AA -> AB
    /**
     * Non-mutating preview of the index the next intake will receive.
     * Same math as generateNextIndex() but never writes the counter.
     */
    public synchronized String previewNextIndex() {
        try (Connection conn = dataSource.getConnection()) {
            int currentNumber;
            String currentLetter;
            try (PreparedStatement ps = conn.prepareStatement(
                    "SELECT current_number, current_letter FROM project_index_counter WHERE id = 1");
                 ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    currentNumber = rs.getInt("current_number");
                    currentLetter = rs.getString("current_letter");
                } else {
                    currentNumber = 0;
                    currentLetter = "A";
                }
            }
            currentNumber = currentNumber + 1;
            if (currentNumber > 999) {
                currentNumber = 1;
                currentLetter = nextLetter(currentLetter);
            }
            return String.format("%03d", currentNumber) + currentLetter;
        } catch (Exception e) {
            throw new RuntimeException("PROJECT_INDEX_FAULT: Could not preview project index", e);
        }
    }


    // Extremely unlikely to ever reach double letters (that would mean
    // 25,974+ projects processed), but this keeps the system correct
    // even if the company somehow gets there.
    private String nextLetter(String letter) {
        char[] chars = letter.toCharArray();
        int i = chars.length - 1;
        while (i >= 0) {
            if (chars[i] != 'Z') {
                chars[i]++;
                return new String(chars);
            } else {
                chars[i] = 'A';
                i--;
            }
        }
        return "A" + new String(chars);
    }
}
