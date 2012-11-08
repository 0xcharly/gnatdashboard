/*
 * Sonar Ada Plugin
 * Copyright (C) 2012, AdaCore
 */
package org.sonar.plugins.ada.codepeer;

import org.sonar.plugins.ada.utils.AdaAbstractRuleRepository;

/**
 * Represent Codepeer rule repository.
 */
public class AdaCodepeerRuleRepository extends AdaAbstractRuleRepository {

    static final String KEY = "codepeer";

    public AdaCodepeerRuleRepository() {
        super(KEY);
        setName(KEY);
    }

    /**
     * Return location of Codepeer rule repository, from resource directory.
     *
     * For now, as it not possible to set a severity to a violation, 4 rules
     * has been created for every Codepeer rule corresponding to each Sonar
     * severity.
     */
    protected String fileName() {
        return "/codepeer.xml";
    }
}
