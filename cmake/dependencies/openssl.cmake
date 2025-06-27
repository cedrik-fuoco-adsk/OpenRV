# Get imported targets before find_package
GET_DIRECTORY_PROPERTY(imported_before IMPORTED_TARGETS)

FIND_PACKAGE(OpenSSL 3.5.0 CONFIG REQUIRED)

# Get imported targets after find_package
GET_DIRECTORY_PROPERTY(imported_after IMPORTED_TARGETS)

# Find the difference (new imported targets)
IF(imported_before)
  LIST(REMOVE_ITEM imported_after ${imported_before})
ENDIF()

MESSAGE(STATUS "cedrik ${openssl_INCLUDE_DIRS_RELEASE}")

IF(imported_after)
  LIST(GET imported_after 0 discovered_target)
  MESSAGE(STATUS "Found imported target: ${discovered_target}")
ELSE()
  MESSAGE(WARNING "No imported targets found")
ENDIF()
