package com.aicoachmastery.coreapi.coach;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

/** Spring Data repository for the Coach aggregate. */
@Repository
public interface CoachRepository extends JpaRepository<Coach, UUID> {

    Optional<Coach> findByEmail(String email);

    boolean existsByEmail(String email);
}
