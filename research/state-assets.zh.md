# SysML v2 状态资产逐文件登记

本表由官方 Pilot 的 typed AST 生成，不通过字符串搜索。每一行保留数据集、相对路径、SHA-256、语法状态节点数、完整校验状态和建议的项目上下文目录。`validated_independent_file` 只表示单文件加标准库通过，`needs_project_index` 表示应在其工程目录整体索引后复核；Apollo 11 使用完整仓库根目录作为项目上下文。

共登记 **122** 个公开状态候选文件。它们不是可执行控制器清单；一个文件可包含多个状态根，状态 usage 也可能是 snapshot 或语义不完整。

| 数据集 | 文件 | SHA-256（前 12 位） | 定义/使用/根 | 语法 | 基线校验 | 上下文目录 |
|---|---|---|---:|---|---|---|
| gfse | `SE_Models/DroneModelLogical.sysml` | `dd8d3e39da78` | 0/6/1 | 错误 | source_validation_error | `SE_Models` |
| gfse | `SE_Models/StopWatchStates.sysml` | `5108f03a4c6c` | 1/4/1 | 有效 | extracted | `SE_Models` |
| gfse | `SE_Models/VehicleModel.sysml` | `edc46afb5e67` | 2/2/4 | 错误 | source_validation_error | `SE_Models` |
| gfse | `example_EveOnlineMiningFrigate/DomainModel/Domain.sysml` | `93917c38b8b7` | 0/1/1 | 有效 | source_validation_error | `example_EveOnlineMiningFrigate/DomainModel` |
| gfse | `example_EveOnlineMiningFrigate/DomainModel/MiningFrigate.sysml` | `ddabb4c84edc` | 0/6/1 | 有效 | source_validation_error | `example_EveOnlineMiningFrigate/DomainModel` |
| gfse | `example_family/family.sysml` | `12ef0a89e951` | 0/3/1 | 有效 | extracted | `example_family` |
| official_pilot | `examples/Arrowhead Framework Example/AHFNorwayTopics.sysml` | `a7b02539744d` | 0/10/4 | 有效 | source_validation_error | `examples/Arrowhead Framework Example` |
| official_pilot | `examples/Interaction Sequencing Examples/ServerSequenceOutsideRealization-2.sysml` | `1c66e402fab3` | 0/3/1 | 有效 | source_validation_error | `examples/Interaction Sequencing Examples` |
| official_pilot | `examples/Interaction Sequencing Examples/ServerSequenceRealization-2.sysml` | `791b64162fb0` | 0/3/1 | 有效 | source_validation_error | `examples/Interaction Sequencing Examples` |
| official_pilot | `examples/Simple Tests/AssignmentTest.sysml` | `7d4b3e646028` | 1/4/2 | 有效 | extracted | `examples/Simple Tests` |
| official_pilot | `examples/Simple Tests/PartTest.sysml` | `488b1646e023` | 0/2/2 | 有效 | extracted | `examples/Simple Tests` |
| official_pilot | `examples/Simple Tests/StateTest.sysml` | `c1e55572d836` | 1/15/5 | 有效 | extracted | `examples/Simple Tests` |
| official_pilot | `examples/Vehicle Example/Annex_A_VehicleViews.sysml` | `c1561aa67531` | 0/11/3 | 有效 | source_validation_error | `examples/Vehicle Example` |
| official_pilot | `examples/Vehicle Example/SysML v2 Spec Annex A SimpleVehicleModel.sysml` | `77d7ee54951e` | 3/25/12 | 有效 | extracted | `examples/Vehicle Example` |
| official_pilot | `training/23. State Definitions/State Definition Example-1.sysml` | `bb96a947ac4f` | 1/3/1 | 有效 | extracted | `training/23. State Definitions` |
| official_pilot | `training/23. State Definitions/State Definition Example-2.sysml` | `52c1ac545553` | 1/3/1 | 有效 | extracted | `training/23. State Definitions` |
| official_pilot | `training/24. States/State Actions.sysml` | `38d8c51cde9c` | 1/4/2 | 有效 | extracted | `training/24. States` |
| official_pilot | `training/24. States/State Decomposition-1.sysml` | `ee8f049bfd5b` | 1/4/2 | 有效 | extracted | `training/24. States` |
| official_pilot | `training/24. States/State Decomposition-2.sysml` | `197be1fb0cc1` | 1/6/2 | 有效 | extracted | `training/24. States` |
| official_pilot | `training/25. Transitions/Change and Time Triggers.sysml` | `3633b959ba8b` | 0/4/1 | 有效 | extracted | `training/25. Transitions` |
| official_pilot | `training/25. Transitions/Local Clock Example.sysml` | `7c4652c10bae` | 0/4/1 | 有效 | extracted | `training/25. Transitions` |
| official_pilot | `training/25. Transitions/Transition Actions.sysml` | `0c2e7db0d37c` | 1/4/2 | 有效 | extracted | `training/25. Transitions` |
| official_pilot | `training/26. State Exhibition/State Exhibition Example.sysml` | `c37cca840710` | 0/1/1 | 有效 | source_validation_error | `training/26. State Exhibition` |
| official_pilot | `training/31. Constraints/Time Constraints.sysml` | `3acc92ed706c` | 0/3/1 | 有效 | extracted | `training/31. Constraints` |
| official_pilot | `validation/05-State-based Behavior/5-State-based Behavior-1.sysml` | `09d33ca09f91` | 2/17/8 | 有效 | source_validation_error | `validation/05-State-based Behavior` |
| official_pilot | `validation/05-State-based Behavior/5-State-based Behavior-1a.sysml` | `22bfc1ae2dbc` | 2/17/8 | 有效 | extracted | `validation/05-State-based Behavior` |
| official_pilot | `validation/05-State-based Behavior/5-State-based Behavior-2.sysml` | `218835c9dbef` | 2/17/8 | 有效 | source_validation_error | `validation/05-State-based Behavior` |
| official_pilot | `validation/06-Individual and Snapshots/6-Individual and Snapshots.sysml` | `31efc993fd2e` | 0/6/4 | 有效 | extracted | `validation/06-Individual and Snapshots` |
| official_pilot | `validation/10-Analysis and Trades/10c-Fuel Economy Analysis.sysml` | `3bea4bbe7b04` | 0/5/1 | 有效 | extracted | `validation/10-Analysis and Trades` |
| refinement_negative | `anthropic/035/iteration_00.sysml` | `565337c0d1e6` | 0/1/1 | 错误 | source_validation_error | `anthropic/035` |
| refinement_negative | `anthropic/052/iteration_00.sysml` | `5210d5a0448b` | 0/1/1 | 错误 | source_validation_error | `anthropic/052` |
| refinement_negative | `anthropic/068/iteration_00.sysml` | `eb66c4f8c5a7` | 0/1/1 | 错误 | source_validation_error | `anthropic/068` |
| refinement_negative | `anthropic/077/iteration_00.sysml` | `71eb956650e5` | 0/1/1 | 错误 | source_validation_error | `anthropic/077` |
| refinement_negative | `anthropic/091/iteration_00.sysml` | `767ae6750f40` | 0/1/1 | 错误 | source_validation_error | `anthropic/091` |
| refinement_negative | `anthropic/102/iteration_00.sysml` | `458351e007ac` | 0/1/1 | 错误 | source_validation_error | `anthropic/102` |
| refinement_negative | `anthropic/104/iteration_00.sysml` | `5ece8afdcc24` | 0/2/2 | 错误 | source_validation_error | `anthropic/104` |
| refinement_negative | `anthropic/107/iteration_00.sysml` | `ad6f3ff688c0` | 0/1/1 | 错误 | source_validation_error | `anthropic/107` |
| refinement_negative | `anthropic/109/iteration_00.sysml` | `849a80bf9f43` | 0/2/2 | 错误 | source_validation_error | `anthropic/109` |
| refinement_negative | `anthropic/114/iteration_00.sysml` | `e7ff174697cc` | 0/2/2 | 错误 | source_validation_error | `anthropic/114` |
| refinement_negative | `anthropic/147/iteration_00.sysml` | `e8e001e09bfc` | 0/5/5 | 错误 | source_validation_error | `anthropic/147` |
| refinement_negative | `deepseek_reasoner/027/iteration_00.sysml` | `7ab53b2a262a` | 0/2/2 | 错误 | source_validation_error | `deepseek_reasoner/027` |
| refinement_negative | `deepseek_reasoner/041/iteration_00.sysml` | `7f9ff25da9d1` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/041` |
| refinement_negative | `deepseek_reasoner/052/iteration_00.sysml` | `6388e3ff90bb` | 0/3/3 | 错误 | source_validation_error | `deepseek_reasoner/052` |
| refinement_negative | `deepseek_reasoner/091/iteration_00.sysml` | `523a6e5fc46b` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/091` |
| refinement_negative | `deepseek_reasoner/091/iteration_01.sysml` | `6388c587b8b1` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/091` |
| refinement_negative | `deepseek_reasoner/104/iteration_00.sysml` | `7e0fa27cc420` | 0/2/2 | 错误 | source_validation_error | `deepseek_reasoner/104` |
| refinement_negative | `deepseek_reasoner/105/iteration_00.sysml` | `673242d38a01` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/105` |
| refinement_negative | `deepseek_reasoner/105/iteration_01.sysml` | `a541090f1f7a` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/105` |
| refinement_negative | `deepseek_reasoner/105/iteration_02.sysml` | `3782ca2ee6af` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/105` |
| refinement_negative | `deepseek_reasoner/106/iteration_00.sysml` | `e9dbb163a46a` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/106` |
| refinement_negative | `deepseek_reasoner/106/iteration_01.sysml` | `182b1a410d7b` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/106` |
| refinement_negative | `deepseek_reasoner/109/iteration_00.sysml` | `870a214fa5e7` | 0/2/2 | 错误 | source_validation_error | `deepseek_reasoner/109` |
| refinement_negative | `deepseek_reasoner/114/iteration_00.sysml` | `7fec5708cea1` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/114` |
| refinement_negative | `deepseek_reasoner/114/iteration_01.sysml` | `d60e3f354358` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/114` |
| refinement_negative | `deepseek_reasoner/134/iteration_00.sysml` | `ed50d7d6c004` | 0/1/1 | 错误 | source_validation_error | `deepseek_reasoner/134` |
| refinement_negative | `mistral_large/027/iteration_00.sysml` | `b8fff130a1f4` | 0/1/1 | 错误 | source_validation_error | `mistral_large/027` |
| refinement_negative | `mistral_large/028/iteration_00.sysml` | `497792c38e6a` | 0/1/1 | 错误 | source_validation_error | `mistral_large/028` |
| refinement_negative | `mistral_large/034/iteration_00.sysml` | `e561d94a2455` | 0/1/1 | 错误 | source_validation_error | `mistral_large/034` |
| refinement_negative | `mistral_large/035/iteration_00.sysml` | `cd05c651c692` | 0/1/1 | 错误 | source_validation_error | `mistral_large/035` |
| refinement_negative | `mistral_large/036/iteration_00.sysml` | `6e7edf3bf9e7` | 0/1/1 | 错误 | source_validation_error | `mistral_large/036` |
| refinement_negative | `mistral_large/036/iteration_01.sysml` | `fe87ce6840c0` | 0/1/1 | 错误 | source_validation_error | `mistral_large/036` |
| refinement_negative | `mistral_large/036/iteration_02.sysml` | `945b486dfd15` | 0/1/1 | 错误 | source_validation_error | `mistral_large/036` |
| refinement_negative | `mistral_large/038/iteration_00.sysml` | `e9920957ed62` | 0/1/1 | 错误 | source_validation_error | `mistral_large/038` |
| refinement_negative | `mistral_large/041/iteration_00.sysml` | `85a89e1272fb` | 0/1/1 | 错误 | source_validation_error | `mistral_large/041` |
| refinement_negative | `mistral_large/042/iteration_00.sysml` | `ea1474174efe` | 0/1/1 | 错误 | source_validation_error | `mistral_large/042` |
| refinement_negative | `mistral_large/042/iteration_01.sysml` | `822d758960f2` | 0/1/1 | 错误 | source_validation_error | `mistral_large/042` |
| refinement_negative | `mistral_large/042/iteration_02.sysml` | `5c1ea8c766e9` | 0/1/1 | 错误 | source_validation_error | `mistral_large/042` |
| refinement_negative | `mistral_large/042/iteration_03.sysml` | `a7f4477283ab` | 0/1/1 | 错误 | source_validation_error | `mistral_large/042` |
| refinement_negative | `mistral_large/052/iteration_00.sysml` | `c9f37cabfcbe` | 0/1/1 | 错误 | source_validation_error | `mistral_large/052` |
| refinement_negative | `mistral_large/078/iteration_00.sysml` | `d353c2e96b23` | 0/1/1 | 错误 | source_validation_error | `mistral_large/078` |
| refinement_negative | `mistral_large/078/iteration_01.sysml` | `be1159abc123` | 0/1/1 | 错误 | source_validation_error | `mistral_large/078` |
| refinement_negative | `mistral_large/102/iteration_00.sysml` | `2e0a9e3c7db8` | 0/1/1 | 错误 | source_validation_error | `mistral_large/102` |
| refinement_negative | `mistral_large/102/iteration_01.sysml` | `e7fd744ea788` | 0/1/1 | 错误 | source_validation_error | `mistral_large/102` |
| refinement_negative | `mistral_large/104/iteration_00.sysml` | `0835ff204098` | 0/1/1 | 错误 | source_validation_error | `mistral_large/104` |
| refinement_negative | `mistral_large/105/iteration_00.sysml` | `4bf4df9eaf3b` | 0/1/1 | 错误 | source_validation_error | `mistral_large/105` |
| refinement_negative | `mistral_large/112/iteration_00.sysml` | `62a1ec1403e9` | 0/1/1 | 错误 | source_validation_error | `mistral_large/112` |
| refinement_negative | `mistral_large/113/iteration_00.sysml` | `5669f4dadf0f` | 0/1/1 | 错误 | source_validation_error | `mistral_large/113` |
| refinement_negative | `mistral_large/114/iteration_00.sysml` | `ce3758ff6bca` | 0/1/1 | 错误 | source_validation_error | `mistral_large/114` |
| refinement_negative | `mistral_large/114/iteration_01.sysml` | `d9d912d151a1` | 0/1/1 | 错误 | source_validation_error | `mistral_large/114` |
| refinement_negative | `openai/018/iteration_00.sysml` | `9193e5cb76fb` | 0/2/2 | 错误 | source_validation_error | `openai/018` |
| refinement_negative | `openai/035/iteration_00.sysml` | `9b0e607c7b37` | 0/1/1 | 错误 | source_validation_error | `openai/035` |
| refinement_negative | `openai/037/iteration_00.sysml` | `ebe8d824073a` | 0/1/1 | 错误 | source_validation_error | `openai/037` |
| refinement_negative | `openai/041/iteration_00.sysml` | `8cbaee34e241` | 0/1/1 | 错误 | source_validation_error | `openai/041` |
| refinement_negative | `openai/042/iteration_00.sysml` | `85c1339278ab` | 0/1/1 | 错误 | source_validation_error | `openai/042` |
| refinement_negative | `openai/043/iteration_00.sysml` | `8239c047ed81` | 0/1/1 | 错误 | source_validation_error | `openai/043` |
| refinement_negative | `openai/043/iteration_01.sysml` | `ca372f90e0c7` | 0/1/1 | 错误 | source_validation_error | `openai/043` |
| refinement_negative | `openai/052/iteration_00.sysml` | `e9531efc17b7` | 0/3/3 | 错误 | source_validation_error | `openai/052` |
| refinement_negative | `openai/052/iteration_02.sysml` | `00eccec2905e` | 0/3/3 | 错误 | source_validation_error | `openai/052` |
| refinement_negative | `openai/060/iteration_00.sysml` | `8d17101a7613` | 0/1/1 | 错误 | source_validation_error | `openai/060` |
| refinement_negative | `openai/077/iteration_00.sysml` | `baf1226af616` | 0/1/1 | 错误 | source_validation_error | `openai/077` |
| refinement_negative | `openai/091/iteration_00.sysml` | `1c087d929cee` | 0/1/1 | 错误 | source_validation_error | `openai/091` |
| refinement_negative | `openai/106/iteration_00.sysml` | `6e87e3d7cf30` | 0/1/1 | 错误 | source_validation_error | `openai/106` |
| refinement_negative | `openai/113/iteration_00.sysml` | `50794b37f1bf` | 0/1/1 | 错误 | source_validation_error | `openai/113` |
| refinement_positive | `mistral_large/035/iteration_01.sysml` | `1f731b9d25da` | 0/1/1 | 有效 | source_validation_error | `mistral_large/035` |
| systemp | `examples/Arrowhead Framework Example/AHFNorwayTopics.sysml` | `ffbda373d3f2` | 0/10/4 | 有效 | source_validation_error | `examples/Arrowhead Framework Example` |
| systemp | `examples/Interaction Sequencing Examples/ServerSequenceOutsideRealization-2.sysml` | `2121a06f2ee7` | 0/3/1 | 有效 | source_validation_error | `examples/Interaction Sequencing Examples` |
| systemp | `examples/Interaction Sequencing Examples/ServerSequenceRealization-2.sysml` | `85df3b3a0c51` | 0/3/1 | 有效 | source_validation_error | `examples/Interaction Sequencing Examples` |
| systemp | `examples/Simple Tests/AssignmentTest.sysml` | `7d4b3e646028` | 1/4/2 | 有效 | extracted | `examples/Simple Tests` |
| systemp | `examples/Simple Tests/PartTest.sysml` | `7d76582141d6` | 0/2/2 | 错误 | source_validation_error | `examples/Simple Tests` |
| systemp | `examples/Simple Tests/StateTest.sysml` | `c39cf365ac35` | 1/8/4 | 有效 | source_validation_error | `examples/Simple Tests` |
| systemp | `training/22. State Definitions/State Definition Example-1.sysml` | `366ba1643b21` | 1/3/1 | 有效 | extracted | `training/22. State Definitions` |
| systemp | `training/22. State Definitions/State Definition Example-2.sysml` | `33670d6848bd` | 1/3/1 | 有效 | extracted | `training/22. State Definitions` |
| systemp | `training/23. States/State Actions.sysml` | `5e73e3d49988` | 1/4/2 | 有效 | extracted | `training/23. States` |
| systemp | `training/23. States/State Decomposition-1.sysml` | `c86e843d014b` | 1/4/2 | 有效 | extracted | `training/23. States` |
| systemp | `training/23. States/State Decomposition-2.sysml` | `c83a12b676a7` | 1/6/2 | 有效 | extracted | `training/23. States` |
| systemp | `training/24. Transitions/Change and Time Triggers.sysml` | `887ca5457b6b` | 0/4/1 | 有效 | source_validation_error | `training/24. Transitions` |
| systemp | `training/24. Transitions/Local Clock Example.sysml` | `0c2c3b11da6a` | 0/4/1 | 有效 | source_validation_error | `training/24. Transitions` |
| systemp | `training/24. Transitions/Transition Actions.sysml` | `72b77cb33600` | 1/4/2 | 有效 | source_validation_error | `training/24. Transitions` |
| systemp | `training/25. State Exhibition/State Exhibition Example.sysml` | `c37cca840710` | 0/1/1 | 有效 | source_validation_error | `training/25. State Exhibition` |
| systemp | `training/30. Constraints/Time Constraints.sysml` | `3acc92ed706c` | 0/3/1 | 有效 | extracted | `training/30. Constraints` |
| systemp | `validation/05-State-based Behavior/5-State-based Behavior-1.sysml` | `38b7005c7de2` | 2/17/8 | 有效 | source_validation_error | `validation/05-State-based Behavior` |
| systemp | `validation/05-State-based Behavior/5-State-based Behavior-1a.sysml` | `b3aa54ce339e` | 2/17/8 | 有效 | source_validation_error | `validation/05-State-based Behavior` |
| systemp | `validation/05-State-based Behavior/5-State-based Behavior-2.sysml` | `7940961fd4be` | 2/17/8 | 有效 | source_validation_error | `validation/05-State-based Behavior` |
| systemp | `validation/06-Individual and Snapshots/6-Individual and Snapshots.sysml` | `31efc993fd2e` | 0/6/4 | 有效 | extracted | `validation/06-Individual and Snapshots` |
| systemp | `validation/10-Analysis and Trades/10c-Fuel Economy Analysis.sysml` | `3bea4bbe7b04` | 0/5/1 | 有效 | extracted | `validation/10-Analysis and Trades` |

| apollo11 | `CoSMA/CoSMAPackage.sysml` | `0a6bf83aa68d` | 1/1/2 | 有效 | extracted | `CoSMA` |
| apollo11 | `Purpose/MissionPackage.sysml` | `f537a72469a6` | 0/16/1 | 有效 | extracted | `Purpose` |
| apollo11 | `Purpose/MissionPhasesPackage.sysml` | `c1e78c28194b` | 15/0/15 | 有效 | extracted | `Purpose` |
| advent | `lesson18/models/L18_SantaSleighCruiseControl_Challenge.sysml` | `2da5fa9040df` | 1/0/1 | 有效 | extracted | `lesson18/models` |
| advent | `lesson18/models/L18_SantaSleighCruiseControl_Solution.sysml` | `f0d24263dd10` | 1/13/1 | 有效 | extracted | `lesson18/models` |
| advent | `lesson18/models/L18_States.sysml` | `e020b385e6d9` | 1/10/1 | 有效 | extracted | `lesson18/models` |
| advent | `lesson19/models/L19_State_Simulation.sysml` | `ef8be64c076c` | 1/7/1 | 有效 | extracted | `lesson19/models` |
机器可读版本：[state-assets.json](state-assets.json)。重新生成：`python research/register_state_assets.py artifacts/syntax-state-inventory.json research/state-assets.json research/state-assets.zh.md`。
