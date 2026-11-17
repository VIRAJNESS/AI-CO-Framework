package com.aicoachmastery.coreapi.config;

import com.aicoachmastery.coreapi.artifact.StageArtifact;
import com.aicoachmastery.coreapi.artifact.StageArtifactRepository;
import com.aicoachmastery.coreapi.engagement.ClientEngagement;
import com.aicoachmastery.coreapi.engagement.ClientEngagementRepository;
import com.aicoachmastery.coreapi.engagement.DomainTrack;
import com.aicoachmastery.coreapi.governance.GateStatus;
import com.aicoachmastery.coreapi.governance.GovernanceGate;
import com.aicoachmastery.coreapi.governance.GovernanceGateRepository;
import com.aicoachmastery.coreapi.mentoring.MentoringProgress;
import com.aicoachmastery.coreapi.mentoring.MentoringProgressRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.OffsetDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.atLeastOnce;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * DataSeeder tests: seeds the 4-engagement showcase only when the database is
 * empty, with correct tracks/stages, 90-day timestamps, deterministic artifact
 * keys and governance statuses.
 */
@ExtendWith(MockitoExtension.class)
class DataSeederTest {

    @Mock
    private ClientEngagementRepository engagements;
    @Mock
    private StageArtifactRepository artifacts;
    @Mock
    private GovernanceGateRepository gates;
    @Mock
    private MentoringProgressRepository mentoring;

    private DataSeeder seeder;

    @BeforeEach
    void setUp() {
        seeder = new DataSeeder(engagements, artifacts, gates, mentoring);
    }

    private void stubSaves() {
        when(engagements.count()).thenReturn(0L);
        when(engagements.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(artifacts.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(gates.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(mentoring.save(any())).thenAnswer(inv -> inv.getArgument(0));
    }

    // --- Happy path ----------------------------------------------------------------

    @Test
    void seedsFourEngagements_coveringAllTracksAndTargetStages() {
        stubSaves();
        seeder.run();

        ArgumentCaptor<ClientEngagement> captor =
                ArgumentCaptor.forClass(ClientEngagement.class);
        verify(engagements, atLeastOnce()).save(captor.capture());
        List<ClientEngagement> seeded = captor.getAllValues();

        assertThat(seeded).hasSize(4);
        assertThat(seeded).extracting(ClientEngagement::getDomainTrack)
                .containsExactlyInAnyOrder(DomainTrack.SDLC, DomainTrack.PDLC,
                        DomainTrack.STARTUP, DomainTrack.LEGACY);
        assertThat(seeded).extracting(ClientEngagement::getCurrentStage)
                .containsExactlyInAnyOrder(6, 4, 3, 2);
        assertThat(seeded).extracting(ClientEngagement::getClientName)
                .contains("NovaTel Global Telecom", "FinPulse Digital Banking",
                        "VeloceAI Series-B SaaS", "OmniCare Core Insurance");
    }

    @Test
    void seedsArtifactsForEveryCompletedStage_withDeterministicKeys() {
        stubSaves();
        seeder.run();

        ArgumentCaptor<StageArtifact> captor = ArgumentCaptor.forClass(StageArtifact.class);
        verify(artifacts, atLeastOnce()).save(captor.capture());
        List<StageArtifact> seeded = captor.getAllValues();

        // NovaTel 6 + FinPulse 4 + VeloceAI 3 + OmniCare 2 = 15 artifacts.
        assertThat(seeded).hasSize(15);
        assertThat(seeded).allSatisfy(artifact -> {
            assertThat(artifact.getPptxFileUrl())
                    .startsWith("showcase/").endsWith(".pptx");
            assertThat(artifact.getDocxFileUrl())
                    .startsWith("showcase/").endsWith(".docx");
        });
        // NovaTel stage 5 carries the statistical proof headline numbers.
        StageArtifact novatelStage5 = seeded.stream()
                .filter(a -> a.getEngagementId().equals(DataSeeder.NOVATEL_ID)
                        && a.getStageNumber() == 5)
                .findFirst().orElseThrow();
        assertThat(novatelStage5.getDiagnosticOutputJson())
                .contains("0.31").contains("0.68").contains("0.86");
    }

    // --- Negative path ---------------------------------------------------------------

    @Test
    void skipsSeeding_whenEngagementsAlreadyExist() {
        when(engagements.count()).thenReturn(3L);

        seeder.run();

        verify(engagements, never()).save(any());
        verify(artifacts, never()).save(any());
        verify(gates, never()).save(any());
        verify(mentoring, never()).save(any());
    }

    // --- Edge cases --------------------------------------------------------------------

    @Test
    void timestampsSpanThePast90Days() {
        // Edge: all created/generated timestamps must be within the last 90 days.
        stubSaves();
        seeder.run();

        ArgumentCaptor<ClientEngagement> engagementCaptor =
                ArgumentCaptor.forClass(ClientEngagement.class);
        verify(engagements, atLeastOnce()).save(engagementCaptor.capture());
        OffsetDateTime now = OffsetDateTime.now();
        OffsetDateTime ninetyDaysAgo = now.minusDays(90);
        assertThat(engagementCaptor.getAllValues())
                .allSatisfy(e -> assertThat(e.getCreatedAt())
                        .isAfter(ninetyDaysAgo).isBefore(now.plusMinutes(1)));

        ArgumentCaptor<StageArtifact> artifactCaptor =
                ArgumentCaptor.forClass(StageArtifact.class);
        verify(artifacts, atLeastOnce()).save(artifactCaptor.capture());
        assertThat(artifactCaptor.getAllValues())
                .allSatisfy(a -> assertThat(a.getGeneratedAt())
                        .isAfter(ninetyDaysAgo).isBefore(now.plusMinutes(1)));
    }

    @Test
    void veloceAiCarriesTheFinOpsFailGate() {
        // Edge: the showcase must include a FAIL gate (demonstrates 409 blocking).
        stubSaves();
        seeder.run();

        ArgumentCaptor<GovernanceGate> captor = ArgumentCaptor.forClass(GovernanceGate.class);
        verify(gates, atLeastOnce()).save(captor.capture());

        assertThat(captor.getAllValues())
                .filteredOn(g -> g.getEngagementId().equals(DataSeeder.VELOCE_ID))
                .filteredOn(g -> g.getStatus() == GateStatus.FAIL)
                .hasSize(1);
    }

    @Test
    void novaTelMentoring_isAtLeadOneMaturity() {
        // Edge: mature client must be in LEAD_ONE across all four role tracks.
        stubSaves();
        seeder.run();

        ArgumentCaptor<MentoringProgress> captor =
                ArgumentCaptor.forClass(MentoringProgress.class);
        verify(mentoring, atLeastOnce()).save(captor.capture());

        List<MentoringProgress> novatel = captor.getAllValues().stream()
                .filter(m -> m.getEngagementId().equals(DataSeeder.NOVATEL_ID))
                .toList();
        assertThat(novatel).hasSize(4);
        assertThat(novatel).allSatisfy(m ->
                assertThat(m.getPhase().name()).isEqualTo("LEAD_ONE"));
    }

    @Test
    void omniCare_hasNoArtifactsBeyondItsCurrentStage() {
        // Edge: stage-2 client must not have stage 3+ artifacts.
        stubSaves();
        seeder.run();

        ArgumentCaptor<StageArtifact> captor = ArgumentCaptor.forClass(StageArtifact.class);
        verify(artifacts, atLeastOnce()).save(captor.capture());

        assertThat(captor.getAllValues())
                .filteredOn(a -> a.getEngagementId().equals(DataSeeder.OMNICARE_ID))
                .allSatisfy(a -> assertThat(a.getStageNumber()).isLessThanOrEqualTo(2));
    }
}
