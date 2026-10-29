package com.gesolutions.erp.modules.land.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockMultipartFile;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/** fix273: documents saved on the server's own disk: clean names, nothing outside the upload folder, delete and wipe. */
class LocalStorageTest {

    @TempDir Path dir;

    @Test
    void savesOpensAndDeletes() throws Exception {
        LocalStorageServiceImpl s = new LocalStorageServiceImpl(dir.toString());
        String folder = "11111111-2222-3333-4444-555555555555";
        MockMultipartFile f = new MockMultipartFile("f", "../../evil name (1).pdf", "application/pdf", "hello".getBytes());

        String addr = s.storeFile(f, folder);
        assertTrue(addr.startsWith("/ge_uploads/" + folder + "/"), addr);
        String[] parts = addr.substring("/ge_uploads/".length()).split("/");
        assertEquals(2, parts.length);
        assertTrue(parts[1].endsWith("_evil_name_1_.pdf"), parts[1]);

        Path p = s.resolveSafe(parts[0], parts[1]);
        assertNotNull(p);
        assertEquals("hello", Files.readString(p));

        // nothing outside the upload folder can be reached
        assertNull(s.resolveSafe("..", "x"));
        assertNull(s.resolveSafe(parts[0], "../x"));
        assertNull(s.resolveSafe("a/b", "c"));
        assertNull(s.resolveSafe(parts[0], ".hidden"));
        assertNull(s.resolveSafe("", "c"));

        s.deleteFile(addr);
        assertFalse(Files.exists(p));
        assertFalse(Files.exists(p.getParent()), "an empty project folder is removed too");
        // an old Cloudinary address or a strange one is skipped without a fault
        s.deleteFile("https://res.cloudinary.com/x/raw/upload/v1/ge_solutions/a/b.pdf");
        s.deleteFile("/ge_uploads/../../etc/passwd");
    }

    @Test
    void wipeRemovesEveryFileAndCountsThem() throws Exception {
        LocalStorageServiceImpl s = new LocalStorageServiceImpl(dir.toString());
        MockMultipartFile f = new MockMultipartFile("f", "a.pdf", "application/pdf", "x".getBytes());
        s.storeFile(f, "one");
        s.storeFile(f, "one");
        s.storeFile(f, "two");
        Map<String, Object> r = s.deleteAllFiles();
        assertEquals(3, r.get("filesDeleted"));
        assertEquals(0, r.get("filesFailed"));
        assertTrue(Files.isDirectory(dir), "the upload folder itself stays");
        try (var left = Files.list(dir)) { assertEquals(0, left.count()); }
    }

    @Test
    void folderDeleteStaysInsideTheUploadFolder() throws Exception {
        LocalStorageServiceImpl s = new LocalStorageServiceImpl(dir.resolve("up").toString());
        MockMultipartFile f = new MockMultipartFile("f", "a.pdf", "application/pdf", "x".getBytes());
        s.storeFile(f, "proj");
        Files.writeString(dir.resolve("keep.txt"), "keep");
        s.deleteFolder("ge_solutions/proj");
        assertFalse(Files.exists(dir.resolve("up").resolve("proj")));
        s.deleteFolder("..");
        s.deleteFolder("ge_solutions/../..");
        assertTrue(Files.exists(dir.resolve("keep.txt")));
    }
}
