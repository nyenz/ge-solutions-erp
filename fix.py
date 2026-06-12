import re

path = "erp-backend/pom.xml"

with open(path, "r") as f:
    content = f.read()

h2_dependency = """
		<!-- H2 DATABASE FOR LOCAL INTEGRATION TESTING -->
		<dependency>
			<groupId>com.h2database</groupId>
			<artifactId>h2</artifactId>
			<scope>test</scope>
		</dependency>
	</dependencies>"""

content = content.replace("</dependencies>", h2_dependency, 1)

with open(path, "w") as f:
    f.write(content)

print("pom.xml patched successfully with H2 test dependency.")