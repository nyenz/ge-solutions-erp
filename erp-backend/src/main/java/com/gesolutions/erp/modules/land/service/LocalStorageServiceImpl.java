// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LocalStorageServiceImpl.java
package com.gesolutions.erp.modules.land.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.lang.NonNull;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Stream;

/**
 * fix273 (David): uploaded documents live on the server's own disk instead of Cloudinary.
 * Switched on with GE_SOLUTIONS_STORAGE=local (the Netcup server). Without it the app keeps using Cloudinary.
 *
 * Where: <upload-dir>/<folder>/<random>_<clean file name>. The address kept in the database is
 * "/ge_uploads/<folder>/<random>_<clean file name>"; the pages already turn that into GET /api/v1/vault/<folder>/<file>
 * with the signed-in person's key (see VaultController), so a document can only be opened by someone logged in.
 * File names are cleaned to letters, digits, dot, dash and underscore, so an address never needs escaping.
 */
@Service
@ConditionalOnProperty(name = "ge.solutions.storage", havingValue = "local")
public class LocalStorageServiceImpl implements FileStorageService {

    private static final String MARKER = "ge_uploads/";
    private final Path base;

    public LocalStorageServiceImpl(@Value("${ge.solutions.upload-dir:/ge_uploads}") String uploadDir) {
        this.base = Paths.get(uploadDir).toAbsolutePath().normalize();
    }

    /** One safe path piece: only letters, digits, dot, dash and underscore. */
    static String clean(String s, int max) {
        String t = s == null ? "" : s.replaceAll("[^A-Za-z0-9._-]", "_").replaceAll("_{2,}", "_").replaceAll("^[._]+", "");
        if (t.length() > max) {
            int dot = t.lastIndexOf('.');
            String ext = (dot > 0 && t.length() - dot <= 8) ? t.substring(dot) : "";
            t = t.substring(0, Math.max(1, max - ext.length())) + ext;
        }
        return t;
    }

    /** The real file for folder + file, or null when it is not a clean name or would leave the upload folder. */
    public Path resolveSafe(String folder, String file) {
        if (folder == null || file == null || folder.isBlank() || file.isBlank()) return null;
        if (!folder.equals(clean(folder, 120)) || !file.equals(clean(file, 160))) return null;
        Path p = base.resolve(folder).resolve(file).normalize();
        return p.startsWith(base) && !p.equals(base) ? p : null;
    }

    @Override
    public String storeFile(@NonNull MultipartFile file, @NonNull String subFolder) throws IOException {
        MultipartFile verified = Objects.requireNonNull(file);
        String folder = clean(Objects.requireNonNull(subFolder), 120);
        if (folder.isEmpty()) folder = "misc";
        String original = verified.getOriginalFilename() == null ? "file" : verified.getOriginalFilename();
        original = original.substring(Math.max(original.lastIndexOf('/'), original.lastIndexOf('\\')) + 1);
        String name = clean(original, 100);
        if (name.isEmpty()) name = "file";
        String stored = UUID.randomUUID().toString().replace("-", "").substring(0, 12) + "_" + name;
        Path dir = base.resolve(folder).normalize();
        if (!dir.startsWith(base)) throw new IOException("Bad folder");
        Files.createDirectories(dir);
        Path target = dir.resolve(stored);
        try (java.io.InputStream in = verified.getInputStream()) {
            Files.copy(in, target, StandardCopyOption.REPLACE_EXISTING);
        }
        System.out.println(">>> LOCAL UPLOAD SUCCESS file=" + folder + "/" + stored);
        return "/ge_uploads/" + folder + "/" + stored;
    }

    /** The file a stored address points to, or null (an old Cloudinary address, or anything not ours). */
    private Path fromAddress(String filePath) {
        if (filePath == null) return null;
        String f = filePath.replace('\\', '/');
        int i = f.indexOf(MARKER);
        if (i < 0 || f.startsWith("http")) return null;
        String[] parts = f.substring(i + MARKER.length()).split("/");
        return parts.length == 2 ? resolveSafe(parts[0], parts[1]) : null;
    }

    @Override
    public void deleteFile(@NonNull String filePath) {
        try {
            Path p = fromAddress(filePath);
            if (p == null) { System.err.println(">>> SKIP DELETE: not a file on this server"); return; }
            Files.deleteIfExists(p);
            Path dir = p.getParent();
            if (dir != null && !dir.equals(base)) {
                try (Stream<Path> left = Files.list(dir)) { if (left.findAny().isEmpty()) Files.deleteIfExists(dir); }
            }
        } catch (Exception e) {
            System.err.println(">>> LOCAL DELETE FAULT: " + e.getMessage());
        }
    }

    @Override
    public void deleteFolder(@NonNull String folderPath) {
        try {
            String f = folderPath.replace('\\', '/');
            if (f.startsWith("ge_solutions/")) f = f.substring("ge_solutions/".length());
            String name = clean(f, 120);
            if (name.isEmpty()) return;
            Path dir = base.resolve(name).normalize();
            if (!dir.startsWith(base) || dir.equals(base) || !Files.isDirectory(dir)) return;
            deleteTree(dir, true);
        } catch (Exception e) {
            System.err.println(">>> LOCAL FOLDER DELETE FAULT: " + e.getMessage());
        }
    }

    private int[] deleteTree(Path root, boolean includeRoot) throws IOException {
        int[] counts = new int[2];   // deleted, failed
        try (Stream<Path> walk = Files.walk(root)) {
            walk.sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
                if (!includeRoot && p.equals(root)) return;
                try {
                    boolean wasFile = Files.isRegularFile(p);
                    Files.deleteIfExists(p);
                    if (wasFile) counts[0]++;
                } catch (IOException | UncheckedIOException e) { counts[1]++; }
            });
        }
        return counts;
    }

    @Override
    public Map<String, Object> deleteAllFiles() {
        Map<String, Object> result = new LinkedHashMap<>();
        int deleted = 0, failed = 0;
        try {
            if (Files.isDirectory(base)) {
                int[] c = deleteTree(base, false);
                deleted = c[0]; failed = c[1];
            }
        } catch (Exception e) {
            failed++;
            result.put("error", "Some files could not be deleted. " + e.getMessage());
        }
        result.put("filesDeleted", deleted);
        result.put("filesFailed", failed);
        if (failed > 0 && !result.containsKey("error")) result.put("error", "Some files could not be deleted.");
        return result;
    }
}
